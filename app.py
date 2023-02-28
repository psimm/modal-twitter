import modal
import twitter
import os
import boto3
import json
import tempfile
import jsonlines
from datetime import datetime

# %%
stub = modal.Stub(
    image=modal.Image.debian_slim().pip_install(["boto3", "python-twitter", "jsonlines"])
)

# %%
@stub.function(secret=modal.Secret.from_name("twitter-api"))
def get_tweets(term: str, count: int, since_id: str = None) -> list:
    # Authenticate with Twitter API
    api = twitter.Api(
        consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
        consumer_secret=os.environ["TWITTER_CONSUMER_SECRET"],
        access_token_key=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_SECRET"],
    )

    return api.GetSearch(
        term=term,
        count=count,
        since_id=since_id,
        lang="en",  # adjust to fetch tweets in other languages
        result_type="recent",
    )

# %%
@stub.function(secret=modal.Secret.from_name("aws-s3-access"))
def save_tweets(filename: str, tweets: list) -> str:
    tweets_dict_list = [t.AsDict() for t in tweets]

    # Convert to JSONL and save to S3
    s3 = boto3.client("s3")

    temp = tempfile.NamedTemporaryFile()
    with jsonlines.open(temp.name, mode="w") as writer:
        writer.write_all(tweets_dict_list)
    
    s3.upload_file(
        Filename=temp.name,
        Bucket=os.environ["S3_BUCKET"],
        Key=filename
    )

    print(f"Saved {len(tweets)} tweets to {filename} on S3")

    since_id = tweets_dict_list[-1]["id"]  # assumes tweets are sorted by id
    return since_id


@stub.function(secret=modal.Secret.from_name("aws-s3-access"))
def get_terms() -> list[dict]:
    s3 = boto3.client("s3")
    terms = json.loads(
        s3.get_object(Bucket=os.environ["S3_BUCKET"], Key="terms.json")["Body"].read()
    )

    # Prioritize terms that have not been searched for recently
    terms = sorted(terms, key=lambda t: (t["timestamp_last_search"], t["since_id"]))
    return terms

# %%
@stub.function(secret=modal.Secret.from_name("aws-s3-access"))
def save_terms(terms: list[dict]) -> None:
    s3 = boto3.client("s3")

    s3.put_object(
        Bucket=os.environ["S3_BUCKET"],
        Key="terms.json",
        Body=json.dumps(terms),
    )
    print("Updated terms.json on S3")

# %%
@stub.function(schedule=modal.Period(minutes=15))
def main():
    terms = get_terms.call()

    print(f"{len(terms)} terms to search: {', '.join([t['term'] for t in terms])}")

    for term in terms:
        print(f"Searching for term: {term['term']}")

        timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        filename = f"{timestamp} {term['term']}.jsonl".replace(" ", "_")

        try:
            tweets = get_tweets.call(term["term"], 100)  # maximum allowed by API
        except Exception as e:
            print(e)
            print("Could not get tweets. Saving tweets collected so far.")
            break

        since_id = save_tweets.call(filename, tweets)  # returns since_id

        # Update values in terms
        term["since_id"] = since_id
        term["timestamp_last_search"] = timestamp

    save_terms.call(terms)

# %%
if __name__ == "__main__":
    with stub.run():
        main.call()
