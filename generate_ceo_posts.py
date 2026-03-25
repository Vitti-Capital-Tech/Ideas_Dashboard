import os
import requests
import json
import re
from datetime import datetime, timezone
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pytz
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_MODEL = "sonar-pro"
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "vitti-ideas-e5256b131985.json")
CEO_LINKEDIN_DOC_ID = os.getenv("CEO_LINKEDIN_DOC_ID")

def fetch_latest_financial_news():
    print("🔍 Fetching latest Australian financial news...")
    prompt = """Search and retrieve 5 of the most significant and trending financial news stories from the past 24-48 hours related to:
    - Australian Stock Exchange (ASX) movements and company news
    - Australian real estate market developments with specific data
    - Private equity and venture capital deals in Australia
    - M&A activity and IPOs in Australian markets
    
    For EACH story, provide:
    1. headline
    2. facts (with numbers)
    3. relevance
    
    OUTPUT AS STRICT RAW JSON ARRAY ONLY. NO MARKDOWN. Format: [{"headline": "...", "facts": "...", "relevance": "..."}]
    """
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2, "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
        content = content.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(content)
        except:
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return fallback_trending_topics()
    except Exception as e:
        print(f"⚠️ Error fetching news: {e}, using fallback...")
        return fallback_trending_topics()

def fallback_trending_topics():
    return [
        {"headline": "Australian Markets Trend Update", "facts": "ASX slightly up, properties stable.", "relevance": "General market movement."}
    ]

def generate_ceo_linkedin_post(news_item):
    context_info = f"Headline: {news_item.get('headline')}\nFacts: {news_item.get('facts')}\nRelevance: {news_item.get('relevance')}"
    
    prompt = f"""You are writing a LinkedIn post for Shubham Goyal, Founder and CEO of VITTI Capital (Sydney-based firm).
    
NEWS/TOPIC:
{context_info}

CRITICAL REQUIREMENTS:
✅ Include SPECIFIC numbers. Show deep institutional insight, not just reporting.
✅ Must have an incredibly catchy, curiosity-inducing headline.
✅ The post MUST sound intimately human and authentic, like a real CEO writing it natively, NOT like a corporate AI robot.
✅ Professional, confident tone. Write like you're advising sophisticated wholesale investors.
✅ End with a compelling question that practically forces readers to comment.
❌ No emojis excessively, no **, no [1]. Strip typical AI jargon.

Write the complete post now:"""
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7, "max_tokens": 2000
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        post = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        post = post.replace("**", "")
        post = re.sub(r'\[\d+\]', '', post)
        return post
    except Exception as e:
        print(f"⚠️ Error generating post: {e}")
        return ""

def append_to_ceo_doc(posts_with_topics):
    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_JSON)
    service = build('docs', 'v1', credentials=creds)
    
    sydney_tz = pytz.timezone("Australia/Sydney")
    today_str = datetime.now(sydney_tz).strftime("%Y-%m-%d %A")
    
    separator = "=" * 60
    content_parts = [f"LinkedIn Content Generated: {today_str}\n{separator}\n\n"]
    
    for idx, item in enumerate(posts_with_topics, 1):
        content_parts.append(f"POST {idx}: {item['topic']}\n")
        content_parts.append("-" * 50 + "\n\n")
        content_parts.append(f"{item['post']}\n\n")
        content_parts.append(separator + "\n\n")
    
    full_text = "".join(content_parts)
    header_len = len(f"LinkedIn Content Generated: {today_str}")
    
    requests_body = [
        {"insertText": {"location": {"index": 1}, "text": full_text}},
        {
            "updateTextStyle": {
                "range": {"startIndex": 1, "endIndex": 1 + header_len},
                "textStyle": {"bold": True, "fontSize": {"magnitude": 14, "unit": "PT"}},
                "fields": "bold,fontSize"
            }
        }
    ]
    
    service.documents().batchUpdate(documentId=CEO_LINKEDIN_DOC_ID, body={"requests": requests_body}).execute()
    print(f"✅ Appended {len(posts_with_topics)} posts to CEO's LinkedIn Doc")

def save_to_logs(posts_with_topics):
    os.makedirs('logs', exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = f"logs/{date_str}-ceo.json"
    
    log_data = {"timestamp": datetime.now().isoformat(), "posts": posts_with_topics}
    
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
            if isinstance(existing, list): existing.append(log_data)
            else: existing = [existing, log_data]
    else:
        existing = [log_data]
        
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=4)
    print(f"✅ Logged to {log_file}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("VITTI CAPITAL - CEO LINKEDIN CONTENT GENERATOR")
    print("="*60 + "\n")
    
    news_items = fetch_latest_financial_news()
    posts_with_topics = []
    
    for idx, item in enumerate(news_items, 1):
        topic_title = item.get('headline', f"Topic {idx}")
        print(f"📝 Generating post {idx}/{len(news_items)}: {topic_title}")
        post = generate_ceo_linkedin_post(item)
        if post:
            posts_with_topics.append({'topic': topic_title, 'post': post})
    
    if posts_with_topics:
        append_to_ceo_doc(posts_with_topics)
        save_to_logs(posts_with_topics)
        print("\n✅ COMPLETE! CEO's LinkedIn content is ready.")
    else:
        print("\n❌ No posts were generated successfully.")
