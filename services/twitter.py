import os
import re
import json
import requests
from requests_oauthlib import OAuth1
import time
from dotenv import load_dotenv


load_dotenv()

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


def _sanitize_cashtags(text: str) -> str:
    """
    Ensures a post contains at most one cashtag. If multiple cashtags are present,
    keep the first cashtag as-is and remove the leading '$' from subsequent cashtags
    so they are not interpreted as cashtags by the X API.
    """
    # Find all cashtags like $SYMBOL or $SYMB.123
    matches = re.findall(r"\$[A-Za-z0-9_.]+", text)
    if len(matches) <= 1:
        return text

    # Replace subsequent cashtags by removing the leading '$'
    count = 0

    def _repl(m):
        nonlocal count
        count += 1
        val = m.group(0)
        if count == 1:
            return val
        return val[1:]

    return re.sub(r"\$[A-Za-z0-9_.]+", _repl, text)


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
        # Sanitize cashtags to avoid X API "maximum of one cashtag" errors
        sanitized_text = _sanitize_cashtags(post_text)

        # Remove hidden unicode characters that can sometimes cause API issues
        sanitized_text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', sanitized_text)

        if sanitized_text != post_text:
            print(f"⚠️ Multiple cashtags detected in post {i+1}; sanitized to avoid API error.")

        payload = {"text": sanitized_text}

        # If it's a thread (subsequent posts), reply to the previous tweet
        if previous_tweet_id:
            payload["reply"] = {
                "in_reply_to_tweet_id": previous_tweet_id
            }

        try:
            print("\n" + "=" * 80)
            print(f"🚀 Posting Tweet {i+1}/{len(posts)}")
            print("=" * 80)

            print(f"Tweet Length: {len(sanitized_text)}")
            print(f"Tweet Content:\n{repr(sanitized_text)}")

            if previous_tweet_id:
                print(f"🔗 Replying To Tweet ID: {previous_tweet_id}")

            print("Payload:")
            print(json.dumps(payload, indent=2))

            response = requests.post(
                url,
                json=payload,
                auth=auth,
                timeout=30
            )

            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")

            response.raise_for_status()

            res_data = response.json()

            print("Parsed Response:")
            print(json.dumps(res_data, indent=2))

            tweet_id = res_data["data"]["id"]

            print(f"Tweet ID Returned: {tweet_id}")
            print(f"Tweet ID Type: {type(tweet_id)}")

            tweet_ids.append(tweet_id)

            print(f"✅ Posted tweet {i+1}/{len(posts)} to X. ID: {tweet_id}")

            previous_tweet_id = tweet_id

            # Give X a few seconds to register the tweet before replying
            if i < len(posts) - 1:
                print("⏳ Waiting 3 seconds before next thread post...")
                time.sleep(3)

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error posting tweet {i+1}: {e}")

            if response is not None:
                print(f"Status Code: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")
                print(f"Response Body: {response.text}")

            print("Failed Payload:")
            print(json.dumps(payload, indent=2))
            break

        except Exception as e:
            print(f"❌ Unexpected error posting tweet {i+1}: {e}")

            print("Failed Payload:")
            print(json.dumps(payload, indent=2))

            if 'response' in locals() and response is not None:
                print(f"Response Body: {response.text}")

            break
    return tweet_ids