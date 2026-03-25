import os
import requests
import json
import re
from datetime import datetime, timezone, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pytz
from dotenv import load_dotenv

load_dotenv()

RAINDROP_TOKEN = os.getenv("RAINDROP_TOKEN")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "vitti-ideas-e5256b131985.json")
GOOGLE_DOC_ID = os.getenv("IDEAS_DOC_ID")
NEW_GOOGLE_DOC_ID = os.getenv("LINKEDIN_POSTS_DOC_ID")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_MODEL = "sonar-pro"

DOC_SIZE_LIMIT = 800_000
TRIM_TARGET = 500_000

def utf16_len(text):
    return len(text.encode("utf-16-le")) // 2

def get_used_bookmarks():
    if os.path.exists('used_bookmarks.txt'):
        with open('used_bookmarks.txt', 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    return set()

def mark_bookmark_used(bm_id):
    if not bm_id: return
    with open('used_bookmarks.txt', 'a', encoding='utf-8') as f:
        f.write(f"{bm_id}\n")

def fetch_raindrop_bookmarks():
    used_bms = get_used_bookmarks()
    headers = {"Authorization": f"Bearer {RAINDROP_TOKEN}"}
    response = requests.get(
        f"https://api.raindrop.io/rest/v1/raindrops/0?perpage=50",
        headers=headers
    )
    if response.status_code != 200:
        print(f"Raindrop Error: {response.text}")
        return []
        
    items = response.json().get("items", [])
    recent_bookmarks = []
    
    for item in items:
        bm_id = str(item.get("_id", ""))
        if bm_id in used_bms:
            continue
        recent_bookmarks.append({
            "id": bm_id,
            "title": item.get("title", ""),
            "excerpt": item.get("excerpt", "")
        })
        if len(recent_bookmarks) >= 5:
            break
            
    return recent_bookmarks

def _call_perplexity(prompt, temperature=0.7):
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 4000
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
    return ""

def generate_ideas(content_item):
    text = f"Title: {content_item.get('title', '')}\nExcerpt: {content_item.get('excerpt', '')}"
    prompt = (
        "Generate 2-3 highly creative and actionable LinkedIn post ideas based on this content. "
        "Each idea should include a catchy title and sub-headings for contents with steps or examples. "
        "Keep it simple and easy to understand. Do not include hashtags or bold text. No References.\n"
        f"{text}"
    )
    return _call_perplexity(prompt, 0.6)

def generate_linkedin_post(content):
    prompt = (
        "Write a highly engaging, thought-provoking LinkedIn post based on this content. "
        "It MUST have a very catchy, curiosity-inducing headline. "
        "The writing style MUST sound completely human, authentic, and conversational—NEVER like an AI robot. "
        "Tell a brief story, share an insight, or state a strong opinion. "
        "Break up paragraphs so it's easy to read (skimmable). "
        "End with a question that practically forces readers to comment. "
        "Do not use emojis excessively. No phrases like 'In today's fast-paced world' or typical AI jargon. "
        "No bolding (**) or citations like [1]. Make it sound like a top-tier LinkedIn creator sharing raw thoughts.\n"
        f"{content}"
    )
    return _call_perplexity(prompt, 0.7)

def fetch_web_ideas(needed_count):
    if needed_count <= 0: return []
    prompt = f"""Search the web for {needed_count} highly trending topics today in tech, AI, startups, or productivity.
    For each topic, provide a brief summary of the news or insight.
    Format as a strict JSON array: [{{"title": "...", "excerpt": "..."}}]
    Do not include any conversational text."""
    content = _call_perplexity(prompt, 0.3)
    try:
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(content)
    except:
        return [{"title": "Trending Tech Topic", "excerpt": content}]

def get_doc_size(service, doc_id):
    doc = service.documents().get(documentId=doc_id).execute()
    content = doc.get("body", {}).get("content", [])
    end_index = content[-1].get("endIndex", 1) if content else 1
    return doc, end_index

def trim_doc_if_needed(service, doc_id, doc_label):
    doc, end_index = get_doc_size(service, doc_id)
    if end_index <= DOC_SIZE_LIMIT: return
    delete_from = TRIM_TARGET
    delete_to = end_index - 1
    if delete_to <= delete_from: return
    service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": [{"deleteContentRange": {"range": {"startIndex": delete_from, "endIndex": delete_to}}}]}
    ).execute()

def _prepend_to_doc(service, doc_id, title_text, body_text):
    full_text = f"{title_text}\n\n{body_text}\n\n"
    service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": [{"insertText": {"location": {"index": 1}, "text": full_text}}]}
    ).execute()

    title_start = 1
    title_end = title_start + utf16_len(title_text)
    body_start = title_start + utf16_len(title_text + "\n\n")
    body_end = title_start + utf16_len(full_text) - 1

    service.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": [
            {
                "updateTextStyle": {
                    "range": {"startIndex": title_start, "endIndex": title_end},
                    "textStyle": {"bold": True, "fontSize": {"magnitude": 18, "unit": "PT"}},
                    "fields": "bold,fontSize"
                }
            },
            {
                "updateTextStyle": {
                    "range": {"startIndex": body_start, "endIndex": body_end},
                    "textStyle": {"bold": False, "fontSize": {"magnitude": 11, "unit": "PT"}},
                    "fields": "bold,fontSize"
                }
            }
        ]}
    ).execute()

def append_to_google_doc(ideas_list, doc_id, label, title_prefix):
    if not ideas_list: return
    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_JSON)
    service = build('docs', 'v1', credentials=creds)
    sydney_tz = pytz.timezone("Australia/Sydney")
    today_str = datetime.now(sydney_tz).strftime("%Y-%m-%d")

    trim_doc_if_needed(service, doc_id, label)

    unique_items = list(dict.fromkeys(ideas_list))
    body_text = "\n\n".join(f"{idx}. {item}" for idx, item in enumerate(unique_items, 1))

    _prepend_to_doc(service, doc_id, f"{title_prefix} for {today_str}", body_text)
    print(f"✅ Prepended {len(unique_items)} items to {label}.")

def save_to_logs(all_ideas, all_posts):
    os.makedirs('logs', exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_file = f"logs/{date_str}-raindrop.json"
    
    log_data = {"timestamp": datetime.now().isoformat(), "ideas": all_ideas, "posts": all_posts}
    
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
    print("="*50)
    print("Raindrop & Web Trends -> LinkedIn Generator")
    print("="*50)
    
    # 1. Fetch Raindrop Bookmarks (up to 5)
    bookmarks = fetch_raindrop_bookmarks()
    
    # 2. Supplement if fewer than 5
    needed = 5 - len(bookmarks)
    if needed > 0:
        print(f"Found {len(bookmarks)} unused bookmarks. Fetching {needed} supplementary web topics...")
        web_topics = fetch_web_ideas(needed)
        bookmarks.extend(web_topics)
    
    all_ideas, all_posts = [], []
    used_ids = []

    # 3. Process each
    for bm in bookmarks:
        print(f"Processing: {bm.get('title', 'Unknown Topic')}")
        ideas = generate_ideas(bm)
        post = generate_linkedin_post(ideas)

        if ideas: all_ideas.append(ideas)
        if post: all_posts.append(post)
            
        if "id" in bm:
            used_ids.append(bm["id"])

    # 4. Save to Docs
    if all_ideas:
        append_to_google_doc(all_ideas, GOOGLE_DOC_ID, "Ideas Doc", "Ideas")
    if all_posts:
        append_to_google_doc(all_posts, NEW_GOOGLE_DOC_ID, "LinkedIn Posts Doc", "LinkedIn Posts")

    # 5. Log and Mark Used
    save_to_logs(all_ideas, all_posts)
    
    for bm_id in used_ids:
        mark_bookmark_used(bm_id)
        
    print("✅ Completed Raindrop Pipeline!")
