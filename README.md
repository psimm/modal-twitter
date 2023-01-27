# Automated Twitter API Data Collector using Modal

Please refer to the accompanying [blog post](https://simmering.dev/blog/modal-twitter/) for a motivation and explanation of the code.

## Installation

1. Clone the repository
2. Install the dependencies via [Poetry](https://python-poetry.org) or pip
3. Create a [Twitter app](https://developer.twitter.com/en) and get the API keys
4. Create an AWS S3 bucket and note the bucket name
5. Create an IAM user with read and write access to the bucket and get the API keys
6. Create a [Modal](https://modal.com) account, and create 2 secrets via the dashboard:

Create a secret named "twitter-api" and add these variables:

```
TWITTER_ACCESS_TOKEN
TWITTER_ACCESS_SECRET
TWITTER_CONSUMER_KEY
TWITTER_CONSUMER_SECRET
```

Create a secret named "aws-s3-access" and add these variables:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
S3_BUCKET
```

7. Adjust the words in `terms.json` to your liking and upload the file to your S3 bucket
8. Run `python app.py` to do a test run
9. Deploy to Modal with `modal deploy --name twitter-data-collector app.py`
