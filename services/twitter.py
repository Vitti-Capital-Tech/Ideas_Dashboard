import os
import re
import json
import requests
from requests_oauthlib import OAuth1

# Use same Sydney Timezone from config if imported, else fallback
try:
    from config import SYDNEY_TZ
except ImportError:
    import pytz
    SYDNEY_TZ = pytz.timezone('Australia/Sydney')


def parse_thread_posts(content: str) -> list[str]:
    """
    Parses the generated LLM text into separate thread posts.
    Splits by 'Post 1', 'Post 2', 'Post 3' (case-insensitive).
    """
    posts = []
    # Split by 'Post [1-3]' with optional colon, dash, or spaces
    parts = re.split(r'(?i)post\s*[1-3][\s\-—:]*', content)
    for part in parts:
        trimmed = part.strip()
        if trimmed:
            posts.append(trimmed)
    return posts


def post_thread_to_x(posts: list[str]) -> list[str]:
    """
    Posts a list of strings as a threaded reply to X (Twitter) using API v2.
    Returns a list of successfully created tweet IDs.
    """
    consumer_key = os.getenv("X_CONSUMER_KEY")
    consumer_secret = os.getenv("X_CONSUMER_SECRET")
    access_token = os.getenv("X_ACCESS_TOKEN")
    access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")

    if not all([consumer_key, consumer_secret, access_token, access_token_secret]):
        print("⚠️ X/Twitter API credentials missing. Skipping automated posting.")
        return []

    auth = OAuth1(consumer_key, consumer_secret, access_token, access_token_secret)
    tweet_ids = []
    previous_tweet_id = None
    url = "https://api.twitter.com/2/tweets"

    for i, post_text in enumerate(posts):
        payload = {"text": post_text}
        
        # If it's a thread (subsequent posts), reply to the previous tweet
        if previous_tweet_id:
            payload["reply"] = {"in_reply_to_tweet_id": previous_tweet_id}

        try:
            response = requests.post(url, json=payload, auth=auth)
            response.raise_for_status()
            res_data = response.json()
            tweet_id = res_data["data"]["id"]
            tweet_ids.append(tweet_id)
            print(f"✅ Posted tweet {i+1}/{len(posts)} to X. ID: {tweet_id}")
            previous_tweet_id = tweet_id
        except Exception as e:
            print(f"❌ Failed to post tweet {i+1} to X: {e}")
            if 'response' in locals() and response is not None:
                print(f"Response: {response.text}")
            break

    return tweet_ids
