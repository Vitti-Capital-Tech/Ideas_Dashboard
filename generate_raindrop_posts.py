import os
import requests
import json
import re
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timezone, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pytz
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

RAINDROP_TOKEN = os.getenv("RAINDROP_TOKEN")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "vitti-ideas-e5256b131985.json")
GOOGLE_DOC_ID = os.getenv("IDEAS_DOC_ID")
# Support both env var names (local .env currently uses CLAUDE_API_KEY).
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
# Use Opus 4.6 by default as requested (can be overridden via ANTHROPIC_MODEL).
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-6")

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

DOC_SIZE_LIMIT = 800_000
TRIM_TARGET = 500_000
DISABLE_GOOGLE_DOC = os.getenv("DISABLE_GOOGLE_DOC", "").strip().lower() in {"1", "true", "yes"}
FALLBACK_ON_LLM_FAILURE = os.getenv("FALLBACK_ON_LLM_FAILURE", "").strip().lower() in {"1", "true", "yes"}

def extract_first_json_array(text):
    """Extract the first complete JSON array of objects or a single JSON object from a string."""
    original_text = text
    text = text.replace("```json", "").replace("```", "").strip()
    
    # Strategy 1: Find every occurrence of '[' (arrays)
    for match in re.finditer(r'\[', text):
        start = match.start()
        after_bracket = text[start+1:].lstrip()
        # Peek ahead: skip citations like [1], but allow objects [{
        if not after_bracket or not after_bracket.startswith('{'):
            continue
            
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
    
    # Strategy 2: If no array was found, search for a top-level JSON object '{ ... }'
    for match in re.finditer(r'\{', text):
        start = match.start()
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]

    # Debug: If still nothing, show the response prefix
    sys_msg = f"  [warn] Extraction failed. Response started with: {original_text[:100]}..."
    print(sys_msg)
    return None

def utf16_len(text):
    return len(text.encode("utf-16-le")) // 2

def get_used_bookmarks():
    if os.path.exists('web/used_bookmarks.txt'):
        with open('web/used_bookmarks.txt', 'r', encoding='utf-8') as f:
            return set(f.read().splitlines())
    return set()

def mark_bookmark_used(bm_id):
    if not bm_id: return
    with open('web/used_bookmarks.txt', 'a', encoding='utf-8') as f:
        f.write(f"{bm_id}\n")

def fetch_raindrop_bookmarks(within_days=5, max_items=5):
    """
    Return up to `max_items` Raindrop bookmarks saved within the last
    `within_days` days that have not been used before.

    Pinned (important=True) items are preferred and sorted first,
    but all recently saved bookmarks qualify regardless of pin status.
    Returns a list of 0..max_items dicts.
    """
    if not RAINDROP_TOKEN:
        print("[warn] RAINDROP_TOKEN not set -- skipping Raindrop fetch.")
        return []

    used_bms = get_used_bookmarks()
    cutoff = datetime.now(timezone.utc) - timedelta(days=within_days)

    headers = {"Authorization": f"Bearer {RAINDROP_TOKEN}"}
    response = requests.get(
        "https://api.raindrop.io/rest/v1/raindrops/0?perpage=50&sort=-created",
        headers=headers,
    )
    if response.status_code != 200:
        print(f"[error] Raindrop API error {response.status_code}: {response.text[:200]}")
        return []

    items = response.json().get("items", [])
    pinned = []
    recent = []

    for item in items:
        bm_id = str(item.get("_id", ""))

        # Skip already-used bookmarks
        if bm_id in used_bms:
            continue

        # Date filter: must have been saved within the last `within_days` days
        created_raw = item.get("created") or item.get("lastUpdate") or ""
        try:
            created_dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
            if created_dt < cutoff:
                continue  # too old — stop scanning (API is sorted newest first)
        except Exception:
            continue

        is_pinned = bool(item.get("important", False))
        bm = {
            "id": bm_id,
            "title": item.get("title", ""),
            "excerpt": item.get("excerpt", ""),
            "url": item.get("link", "") or item.get("url", ""),
            "pinned": is_pinned,
            "source_type": "raindrop",
            "created": created_raw,
        }
        (pinned if is_pinned else recent).append(bm)

    # Pinned first, then newest saved — cap to max_items
    qualified = (pinned + recent)[:max_items]
    print(f"  [raindrop] {len(pinned)} pinned + {len(recent)} recent = "
          f"{len(qualified)} selected (last {within_days} days)")
    return qualified

def _call_claude(prompt, temperature=0.4, max_tokens=4000):
    if not anthropic_client:
        print("[error] ANTHROPIC_API_KEY (or CLAUDE_API_KEY) is missing!")
        return ""

    last_err = None
    for attempt in range(1, 4):
        try:
            msg = anthropic_client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            parts = []
            for block in getattr(msg, "content", []) or []:
                if getattr(block, "type", None) == "text":
                    parts.append(block.text)
            return "\n".join(parts).strip()
        except Exception as e:
            last_err = e
            err_text = str(e).lower()
            retriable = ("529" in err_text) or ("overloaded" in err_text) or ("rate" in err_text) or ("timeout" in err_text)
            if attempt < 3 and retriable:
                sleep_s = 2 * attempt
                print(f"[warn] Claude transient error (attempt {attempt}/3). Retrying in {sleep_s}s.")
                time.sleep(sleep_s)
                continue
            break

    print(f"[error] Claude call failed: {last_err}")
    return ""

def _normalize_idea_fields(idea):
    """
    LLMs often omit context/angle or use alternate keys. Merge so filtering does not drop good titles.
    """
    if not isinstance(idea, dict):
        return idea
    lp = idea.get("linkedin_playbook")
    if isinstance(lp, dict):
        # Model typo tolerance
        if lp.get("why_this_worksd") and not lp.get("why_this_works"):
            lp["why_this_works"] = lp.get("why_this_worksd")
        if not _safe_text(idea.get("context")):
            blob = " ".join(
                _safe_text(str(x))
                for x in (
                    lp.get("opening_hook"),
                    lp.get("why_section"),
                    lp.get("unique_take"),
                    lp.get("call_to_action"),
                )
                if x
            )
            if blob:
                idea["context"] = blob
        if not _safe_text(idea.get("angle")):
            ang = _safe_text(lp.get("unique_take")) or _safe_text(lp.get("why_this_works"))
            if ang:
                idea["angle"] = ang
        if not _safe_text(idea.get("title")):
            idea["title"] = _safe_text(lp.get("opening_hook", ""))[:200] or "LinkedIn idea"
    # Flatten common alternate key casings / names
    aliases = {
        "context": ["context", "Context", "summary", "Summary", "body", "Body", "narrative", "overview"],
        "angle": ["angle", "Angle", "insight", "Insight", "takeaway", "Takeaway", "why_it_matters", "key_takeaway"],
        "title": ["title", "Title", "hook", "Hook"],
    }
    for canonical, keys in aliases.items():
        for k in keys:
            if k in idea and idea.get(k) is not None and _safe_text(str(idea.get(k))):
                if canonical not in idea or not _safe_text(str(idea.get(canonical))):
                    idea[canonical] = idea.get(k)
                break
    # Backfill context from pager markdown if still empty
    ctx = _safe_text(idea.get("context"))
    if not ctx:
        pages = (idea.get("content") or {}).get("pages") or []
        for p in pages:
            md = _safe_text((p or {}).get("markdown") or "")
            if len(md) > 80:
                idea["context"] = md[:500] + ("..." if len(md) > 500 else "")
                break
    # Backfill angle from grounding / last resort
    ang = _safe_text(idea.get("angle"))
    if not ang:
        used = (idea.get("grounding") or {}).get("sources_used") or []
        if used:
            idea["angle"] = (
                "Compare and stress-test the signals above: what changes for allocation, risk, or ops when these sources are read together?"
            )
        else:
            idea["angle"] = "What is the non-obvious implication for finance or strategy once cross-checked across sources?"
    return idea


def parse_and_filter_ideas(raw_ideas_str):
    """Parse JSON output and reject generic/ungrounded ideas."""
    if not raw_ideas_str:
        return []
    try:
        json_str = extract_first_json_array(raw_ideas_str)
        if not json_str:
            return []
        ideas = json.loads(json_str)
        if isinstance(ideas, dict):
            ideas = [ideas]
    except Exception as e:
        print(f"  [warn] Could not parse ideas JSON: {e}")
        return []

    GENERIC_PHRASES = [
        "consistency is key", "hard work pays off", "believe in yourself",
        "embrace the journey", "think outside the box", "leverage", "synergy",
        "in today's world", "fast-paced", "game changer", "disrupt"
    ]

    filtered = []
    for idea in ideas:
        if not isinstance(idea, dict):
            continue
        idea = _normalize_idea_fields(idea)
        title = _safe_text(idea.get("title", "")).lower()
        context = _safe_text(idea.get("context", "")).lower()
        angle = _safe_text(idea.get("angle", ""))
        # Reject if missing required fields (after normalization)
        if not title or not context or not angle:
            print(f"  [warn] REJECTED (missing fields): {idea.get('title', '')[:60]}")
            continue
        # Reject generic phrases
        if any(phrase in title or phrase in context for phrase in GENERIC_PHRASES):
            print(f"  [warn] REJECTED (generic): {idea.get('title', '')[:60]}")
            continue
        filtered.append(idea)
    return filtered

def _safe_text(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def _parse_rss_pubdate(pubdate_text):
    if not pubdate_text:
        return None
    # Common RSS dates: "Wed, 01 Apr 2026 03:12:00 GMT"
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(pubdate_text)
    except Exception:
        return None


def fetch_trending_finance_news(count=8, within_hours=48):
    """
    Fetch trending finance/business news via RSS (no Perplexity dependency).
    Returns list of {title, excerpt, url, source_type, region}.
    """
    feeds = [
        # Finance & Trading news (Australia focused + Global Macro)
        "https://news.google.com/rss/search?q=Australia+ASX200+stock+market+trading+when:2d&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=Reserve+Bank+of+Australia+RBA+interest+rates+economy+when:2d&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=global+stock+markets+S%26P500+Wall+Street+when:2d&hl=en-US&gl=US&ceid=US:en",
    ]

    cutoff = datetime.now(timezone.utc) - timedelta(hours=within_hours)
    items = []

    for feed_url in feeds:
        try:
            resp = requests.get(feed_url, timeout=30)
            if resp.status_code != 200 or not resp.text:
                continue
            root = ET.fromstring(resp.text)
            channel = root.find("channel")
            if channel is None:
                continue
            for it in channel.findall("item"):
                title = _safe_text((it.findtext("title") or "").replace(" - Google News", ""))
                link = _safe_text(it.findtext("link") or "")
                desc = _safe_text(it.findtext("description") or "")
                pub = _parse_rss_pubdate(_safe_text(it.findtext("pubDate") or ""))
                if pub and pub.tzinfo is None:
                    pub = pub.replace(tzinfo=timezone.utc)
                if pub and pub < cutoff:
                    continue
                if not title:
                    continue
                items.append({
                    "title": title,
                    "excerpt": desc[:400],
                    "url": link,
                    "source_type": "news",
                    "region": "Australia" if "AU:en" in feed_url or "Australia" in feed_url else "Global",
                    "published_at": pub.isoformat() if pub else None,
                })
        except Exception:
            continue

    # De-dupe by title
    seen = set()
    deduped = []
    for it in items:
        key = it.get("title", "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(it)
        if len(deduped) >= count:
            break

    return deduped


def fetch_trending_tech_news(count=6, within_hours=48):
    """
    Fetch trending tech/AI/product news via RSS.
    Returns list of {title, excerpt, url, source_type, region}.
    """
    feeds = [
        # Market segments (Commodities, Forex, Crypto/Algo Trading)
        "https://news.google.com/rss/search?q=Australia+commodities+iron+ore+gold+trading+when:2d&hl=en-AU&gl=AU&ceid=AU:en",
        "https://news.google.com/rss/search?q=forex+AUD+USD+currency+trading+markets+when:2d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=crypto+Bitcoin+algorithmic+trading+quant+when:2d&hl=en-US&gl=US&ceid=US:en",
    ]

    cutoff = datetime.now(timezone.utc) - timedelta(hours=within_hours)
    items = []
    for feed_url in feeds:
        try:
            resp = requests.get(feed_url, timeout=30)
            if resp.status_code != 200 or not resp.text:
                continue
            root = ET.fromstring(resp.text)
            channel = root.find("channel")
            if channel is None:
                continue
            for it in channel.findall("item"):
                title = _safe_text((it.findtext("title") or "").replace(" - Google News", ""))
                link = _safe_text(it.findtext("link") or "")
                desc = _safe_text(it.findtext("description") or "")
                pub = _parse_rss_pubdate(_safe_text(it.findtext("pubDate") or ""))
                if pub and pub.tzinfo is None:
                    pub = pub.replace(tzinfo=timezone.utc)
                if pub and pub < cutoff:
                    continue
                if not title:
                    continue
                items.append({
                    "title": title,
                    "excerpt": desc[:400],
                    "url": link,
                    "source_type": "tech",
                    "region": "Australia" if "AU:en" in feed_url or "Australia" in feed_url else "Global",
                    "published_at": pub.isoformat() if pub else None,
                })
        except Exception:
            continue

    seen = set()
    deduped = []
    for it in items:
        key = it.get("title", "").lower()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(it)
        if len(deduped) >= count:
            break
    return deduped


def _tokenize(text):
    words = re.findall(r"[a-zA-Z0-9]{3,}", (text or "").lower())
    stop = {
        "the","and","for","with","from","that","this","into","are","was","were","has","have",
        "will","your","you","its","but","not","about","over","after","before","near","more",
        "when","what","why","how","their","they","them","than","then","also","into","across",
        "news","google","said","says","new","update","today","report"
    }
    return [w for w in words if w not in stop]


def attach_cross_verification(anchors, external_items, per_anchor=2):
    """
    For each anchor (Raindrop or web), attach related items from another pool
    so nothing is passed to the LLM as a single isolated source.
    """
    if not anchors:
        return []

    ext = external_items or []
    ext_tokens = []
    for it in ext:
        t = _tokenize((it.get("title", "") + " " + it.get("excerpt", "")))
        ext_tokens.append((it, set(t)))

    out = []
    for bm in anchors:
        bm_tokens = set(_tokenize((bm.get("title", "") + " " + bm.get("excerpt", ""))))
        scored = []
        for it, toks in ext_tokens:
            # Prefer different URL/title so cross-check is not the same story twice
            if it.get("url") == bm.get("url") and bm.get("url"):
                continue
            score = len(bm_tokens.intersection(toks))
            if score > 0:
                scored.append((score, it))
        scored.sort(key=lambda x: x[0], reverse=True)
        related = [it for _, it in scored[:per_anchor]]
        # If overlap matching is weak, still attach diverse items from ext (finance + tech mix)
        if len(related) < per_anchor:
            seen_urls = {bm.get("url"), *[x.get("url") for x in related]}
            for it, _ in ext_tokens:
                if len(related) >= per_anchor:
                    break
                u = it.get("url") or ""
                if u and u in seen_urls:
                    continue
                related.append(it)
                if u:
                    seen_urls.add(u)
        bm2 = dict(bm)
        bm2["cross_verify"] = related[:per_anchor]
        out.append(bm2)
    return out


def pick_diverse_web_anchors(finance_items, tech_items, count=5):
    """
    When Raindrop has nothing usable, pick up to `count` anchors from the web pool
    mixing finance + tech so we are not dependent on one feed or one story type.
    """
    fin = list(finance_items or [])
    tech = list(tech_items or [])
    anchors = []
    seen = set()
    i, j = 0, 0
    while len(anchors) < count and (i < len(fin) or j < len(tech)):
        if len(anchors) % 2 == 0 and i < len(fin):
            a = dict(fin[i])
            i += 1
        elif j < len(tech):
            a = dict(tech[j])
            j += 1
        elif i < len(fin):
            a = dict(fin[i])
            i += 1
        else:
            break
        a.setdefault("source_type", "news")
        if not a.get("url"):
            a["url"] = ""
        key = a.get("url") or a.get("title", "")
        if key in seen:
            continue
        seen.add(key)
        anchors.append(a)
    # If still short, fill from whichever list has items left
    for pool in (fin, tech):
        for x in pool:
            if len(anchors) >= count:
                break
            a = dict(x)
            a.setdefault("source_type", "news")
            key = a.get("url") or a.get("title", "")
            if key in seen:
                continue
            seen.add(key)
            anchors.append(a)
        if len(anchors) >= count:
            break
    return anchors[:count]


def dedupe_source_list(items):
    """Stable de-dupe by url then title."""
    seen = set()
    out = []
    for x in items or []:
        k = (x.get("url") or "").strip() or (x.get("title") or "").strip()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(x)
    return out


def fetch_url_snippet(url, max_chars=600, timeout=8):
    """
    Lightweight fetch of public HTML pages to enrich excerpts (best-effort, no JS).
    """
    if not url or not url.startswith("http"):
        return ""
    try:
        r = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; VittiIdeasBot/1.0)"},
        )
        if r.status_code != 200 or not r.text:
            return ""
        text = re.sub(r"(?is)<script.*?>.*?</script>", " ", r.text)
        text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = _safe_text(text)
        return text[:max_chars]
    except Exception:
        return ""


def generate_daily_connected_ideas(sources, ideas_per_day=5, source_mode="raindrop_plus_web"):
    """
    Single Claude call: one dedicated idea per anchor source, each independently themed.
    Web cross_verify items validate/enrich each anchor but cannot dominate.

    source_mode:
      - "raindrop_plus_web": Raindrop bookmarks are anchors; web is context/verification
      - "web_only": diverse web items are anchors; other web items are context/verification
    """
    sources = sources or []

    # Separate anchors (items with cross_verify) from pure context sources
    anchor_items = []
    context_pool = []
    for s in sources:
        cv = s.get("cross_verify") or []
        entry = {
            "source_type": s.get("source_type", "news"),
            "title": _safe_text(s.get("title")),
            "excerpt": _safe_text(s.get("excerpt")),
            "url": _safe_text(s.get("url", "")),
            "region": _safe_text(s.get("region", "")),
            "pinned": bool(s.get("pinned", False)),
            "cross_verify": [
                {
                    "source_type": x.get("source_type", "news"),
                    "title": _safe_text(x.get("title")),
                    "excerpt": _safe_text(x.get("excerpt", ""))[:300],
                    "url": _safe_text(x.get("url", "")),
                }
                for x in cv
            ],
        }
        if cv:
            anchor_items.append(entry)
        else:
            ctx = {k: v for k, v in entry.items() if k != "cross_verify"}
            context_pool.append(ctx)

    # Ensure we have exactly ideas_per_day anchors labelled
    anchors_for_prompt = anchor_items[:ideas_per_day]

    if source_mode == "raindrop_plus_web":
        mode_rules = f"""SOURCE MODE: Raindrop bookmarks + web cross-check
- The ANCHORS array contains {len(anchors_for_prompt)} items. Generate EXACTLY ONE idea per anchor — in the same order.
- Raindrop anchors (source_type="raindrop") must be the PRIMARY subject of their idea. Do not reuse any anchor as the primary for a second idea.
- Each idea's cross_verify items are web sources to VALIDATE or CHALLENGE the anchor angle — cite at least one per idea.
- Ideas must be INDEPENDENTLY themed: Idea 1 is about anchor 1's topic, Idea 2 is about anchor 2's topic, etc.
- Do NOT create one overarching series thesis that forces all ideas onto the same topic."""
    else:
        mode_rules = f"""SOURCE MODE: Web-only (no Raindrop bookmarks today)
- The ANCHORS array contains {len(anchors_for_prompt)} diverse web stories. Generate EXACTLY ONE idea per anchor — in the same order.
- Each anchor is the PRIMARY subject of its idea. Do not reuse any anchor as primary for another idea.
- Use cross_verify items to add a second independent perspective (agreement, tension, or gap).
- Ideas must cover DISTINCT topics — do not force one narrative across all five."""

    prompt = f"""You are a finance + tech content strategist for Vitti Capital.

TASK:
Generate EXACTLY {ideas_per_day} LinkedIn content ideas — one dedicated idea per ANCHOR SOURCE below.
Each idea must be independently themed based on its anchor's topic.

{mode_rules}

ANCHOR-TO-IDEA MAPPING RULE (CRITICAL):
- Anchor 1 → Idea 1. Anchor 2 → Idea 2. And so on.
- The anchor is the headline and primary evidence for that idea.
- The cross_verify items add a second voice but must not override the anchor's core topic.
- NEVER use the same anchor URL as the primary source in more than one idea.
- Each idea must have a DIFFERENT topic, hook, and takeaway.

GLOBAL QUALITY RULES:
- Cross-verification is mandatory: each idea must explicitly state how the cross_verify item confirms, contradicts, or narrows the anchor angle.
- Context: tight research synthesis — what the anchor says + what the cross_verify adds. Do not pad.
- Draft (markdown): publishable LinkedIn post, 150-280 words. Professional, thought-leadership tone. No clickbait. No invented statistics.
- Australian finance lens where relevant; global where not.
- Each idea MUST use a DIFFERENT LinkedIn format (no repeats across the {ideas_per_day} ideas).

LINKEDIN FORMATS (use each at most once):
1) "Industry Trend Interpretation" — surprising hook on a live trend, why it matters, unique read vs headlines, CTA question.
2) "Before/After Results Story" — challenge, turning point, outcome (grounded metrics only), invitation to share.
3) "Provocative Question & Poll Hybrid" — contrarian setup, poll options (3-4), 2-3 lines why now, CTA to comment.
4) "Contrarian Institution Read" — what consensus misses, evidence from sources, risk of being wrong, one sharp question.
5) "Signal Decoder" — what the signal is, second source confirming or tensioning it, practical implication for operators/investors.

OUTPUT:
Return strict JSON array ONLY (no markdown, no commentary). EXACTLY {ideas_per_day} objects, one per anchor in order.
Schema:
[
  {{
    "anchor_source": "url of the anchor this idea is based on",
    "title": "Working title for the post",
    "context": "2-4 sentences: what the anchor says + how cross_verify confirms/challenges it (required)",
    "angle": "One-line strategic takeaway",
    "linkedin_playbook": {{
      "format_name": "One of the five format names above",
      "opening_hook": "Scroll-stopping opening line or short paragraph",
      "why_section": "Broader implications for professionals / markets",
      "unique_take": "Perspective beyond the headline, grounded in both anchor and cross_verify",
      "call_to_action": "Ending question or invitation (exactly one)",
      "why_this_works": "1-2 sentences: why this format earns engagement for this audience",
      "poll_options": ["Option A", "Option B", "Option C", "Option D"]
    }},
    "grounding": {{
      "sources_used": [
        {{"source_type": "raindrop|news|tech|web", "title": "...", "url": "..."}}
      ]
    }},
    "region": "Australia|Global|Mixed",
    "source_type": "raindrop|news|hybrid",
    "content": {{
      "format": "1-pager",
      "pages": [
        {{
          "page_title": "Draft",
          "markdown": "Full LinkedIn-ready draft, 150-280 words. Hook through CTA. No fake citations."
        }}
      ]
    }}
  }}
]

Note: If the format is not poll-based, set poll_options to [] (empty array).

ANCHORS (one idea per anchor, in order):
{json.dumps(anchors_for_prompt, ensure_ascii=False)}

ADDITIONAL CONTEXT (use for cross-verification only, not as primary anchors):
{json.dumps(context_pool[:10], ensure_ascii=False)}

Generate now:"""

    raw = _call_claude(prompt, temperature=0.35, max_tokens=12000)
    return raw






def fallback_connected_ideas(sources, ideas_per_day=5):
    """
    Deterministic fallback used only when FALLBACK_ON_LLM_FAILURE=1.
    Produces minimal valid objects so the pipeline can still write logs.
    """
    srcs = sources or []
    pick = srcs[: max(ideas_per_day * 2, ideas_per_day)]
    series_title = "Daily Macro x Tech Cross-Check"
    series_thesis = "A connected set of prompts linking current finance signals with tech/platform shifts to stress-test assumptions."
    ideas = []
    for i in range(ideas_per_day):
        a = pick[i] if i < len(pick) else {}
        b = pick[i + 1] if (i + 1) < len(pick) else {}
        a_title = _safe_text(a.get("title")) or f"Signal {i+1}"
        b_title = _safe_text(b.get("title")) or "External cross-check"
        ideas.append({
            "series_title": series_title,
            "series_thesis": series_thesis,
            "title": f"{i+1}) {a_title} -> {b_title}",
            "context": "Fallback mode: LLM unavailable. Use the sources below to draft a grounded angle and add verification details.",
            "angle": "Turn this into a finance-first insight by extracting concrete numbers/entities from the linked sources.",
            "connections": {"builds_on": "Continues the same thesis with the next pair of signals." if i > 0 else "Starts the series thesis."},
            "grounding": {"sources_used": [
                {"source_type": a.get("source_type", "news"), "title": a_title, "url": a.get("url", "")},
                {"source_type": b.get("source_type", "news"), "title": b_title, "url": b.get("url", "")},
            ]},
            "region": "Mixed",
            "source_type": "hybrid",
            "content": {
                "format": "1-pager",
                "pages": [{
                    "page_title": "Pager draft (fallback)",
                    "markdown": f"## Sources\n- {a_title}\n- {b_title}\n\n## Notes\n- Add numbers/entities\n- Add cross-verification\n- Draft 5-bullet takeaway"
                }]
            }
        })
    return json.dumps(ideas, ensure_ascii=False)

def format_ideas_for_doc(ideas_structured):
    """Convert structured idea dicts into clean human-readable text for Google Docs."""
    lines = []
    for idx, idea in enumerate(ideas_structured, 1):
        lines.append(f"LINKEDIN POST IDEA {idx}: {idea.get('title', 'Untitled')}")
        lp = idea.get("linkedin_playbook") or {}
        if isinstance(lp, dict) and lp.get("format_name"):
            lines.append(f"Format  : {lp.get('format_name')}")
            lines.append(f"Opening hook   : {lp.get('opening_hook', 'N/A')}")
            lines.append(f"Why (implications) : {lp.get('why_section', 'N/A')}")
            lines.append(f"Unique take : {lp.get('unique_take', 'N/A')}")
            lines.append(f"CTA : {lp.get('call_to_action', 'N/A')}")
            opts = lp.get("poll_options") or []
            if opts:
                lines.append(f"Poll options : {', '.join(str(o) for o in opts)}")
            lines.append(f"Why this works : {lp.get('why_this_works', 'N/A')}")
        lines.append(f"Context : {idea.get('context', 'N/A')}")
        lines.append(f"Angle   : {idea.get('angle', 'N/A')}")
        lines.append(f"Builds on : {(idea.get('connections') or {}).get('builds_on', 'N/A')}")
        gu = (idea.get("grounding") or {}).get("sources_used") or []
        for s in gu[:8]:
            lines.append(f"  - [{s.get('source_type','?')}] {s.get('title','')} {s.get('url','')}")
        lines.append(f"Source  : {idea.get('source_type', 'N/A').upper()}  |  Region: {idea.get('region', 'N/A')}")
        pages = (idea.get("content") or {}).get("pages") or []
        if pages:
            lines.append("Draft (markdown):")
            lines.append((pages[0] or {}).get("markdown", "")[:4000])
        lines.append("-" * 50)
    return "\n".join(lines)

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
    if DISABLE_GOOGLE_DOC:
        print("[info] Google Doc write disabled (DISABLE_GOOGLE_DOC=1).")
        return
    if not doc_id:
        print("[info] IDEAS_DOC_ID missing — skipping Google Doc write.")
        return
    if not GOOGLE_CREDENTIALS_JSON or not os.path.exists(GOOGLE_CREDENTIALS_JSON):
        print(f"[info] Google credentials file not found ({GOOGLE_CREDENTIALS_JSON}) — skipping Google Doc write.")
        return
    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_JSON)
    service = build('docs', 'v1', credentials=creds)
    sydney_tz = pytz.timezone("Australia/Sydney")
    today_str = datetime.now(sydney_tz).strftime("%Y-%m-%d")

    trim_doc_if_needed(service, doc_id, label)

    unique_items = list(dict.fromkeys(ideas_list))
    body_text = "\n\n".join(f"{idx}. {item}" for idx, item in enumerate(unique_items, 1))

    _prepend_to_doc(service, doc_id, f"{title_prefix} for {today_str}", body_text)
    print(f"[ok] Prepended {len(unique_items)} items to {label}.")

def _load_log_file(path):
    """Load a JSON log file, returning [] if missing or empty/corrupt."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except (json.JSONDecodeError, ValueError):
        print(f"  [warn] Log file {path} was empty or corrupt — starting fresh.")
        return []

def save_to_logs(all_ideas_structured, all_posts):
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Save Ideas (structured dicts — clean for webapp rendering)
    if all_ideas_structured:
        os.makedirs('web/logs', exist_ok=True)
        ideas_file = f"web/logs/{date_str}.json"
        log_data = {"timestamp": datetime.now().isoformat(), "ideas": all_ideas_structured}
        existing = _load_log_file(ideas_file)
        existing.append(log_data)
        with open(ideas_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=4)
        print(f"[ok] Ideas logged to {ideas_file}")
    # Posts are no longer generated; dashboard is Ideas-only.

if __name__ == "__main__":
    print("=" * 50)
    print("VITTI CAPITAL - Daily Ideas Pack Generator")
    print("=" * 50)

    IDEAS_PER_DAY = 5

    # -- 1. Raindrop: pinned bookmarks saved in the last 5 days ---------------
    print("\nFetching Raindrop bookmarks (pinned, last 5 days)...")
    raindrop_items = fetch_raindrop_bookmarks(within_days=5, max_items=IDEAS_PER_DAY)
    print(f"Found {len(raindrop_items)} qualifying Raindrop item(s) (pinned + <=5 days old).")

    # Enrich excerpts for Raindrop items that have no snippet
    for bm in raindrop_items:
        bm["source_type"] = "raindrop"
        if not bm.get("excerpt") and bm.get("url"):
            snip = fetch_url_snippet(bm["url"])
            if snip:
                bm["excerpt"] = snip[:500]

    # -- 2. Live web RSS -- always fetch for cross-verification + potential fill
    print("\nFetching trending finance news via RSS...")
    finance_items = fetch_trending_finance_news(count=14, within_hours=48)
    print(f"Found {len(finance_items)} finance items.")

    print("Fetching trending tech news via RSS...")
    tech_items = fetch_trending_tech_news(count=12, within_hours=48)
    print(f"Found {len(tech_items)} tech items.")

    external_items = finance_items + tech_items

    if not external_items:
        print("[error] No web sources available (RSS empty). Cannot cross-verify. Exiting.")
        exit(1)

    # -- 3. Build anchor list -- Raindrop first, top up with web if needed ----
    n_rain = len(raindrop_items)
    deficit = IDEAS_PER_DAY - n_rain  # how many web fill-ins we need

    used_ids = []        # only Raindrop IDs get marked as used
    web_fill_items = []  # web items used as anchors (not marked used)

    if deficit > 0:
        # Pick diverse web stories to fill the gap
        rain_urls = {bm.get("url") or bm.get("title", "") for bm in raindrop_items}
        candidate_pool = [x for x in external_items
                          if (x.get("url") or x.get("title", "")) not in rain_urls]
        web_fill_items = pick_diverse_web_anchors(
            [x for x in candidate_pool if x.get("source_type") == "news"],
            [x for x in candidate_pool if x.get("source_type") == "tech"],
            count=deficit,
        )
        if len(web_fill_items) < deficit:
            # If still short, just take whatever is available
            web_fill_items = candidate_pool[:deficit]
        print(f"[info] Filling {deficit} slot(s) with web anchors "
              f"({len(web_fill_items)} selected).")

    # Combined anchor list: Raindrop items + web fill-ins
    anchor_items = raindrop_items + web_fill_items

    if not anchor_items:
        print("[error] No anchors available at all (Raindrop empty, web RSS also empty).")
        exit(1)

    # IDs to mark used -- Raindrop only
    used_ids = [bm.get("id") for bm in raindrop_items if bm.get("id")]

    # Set source mode
    source_mode = "raindrop_plus_web" if n_rain > 0 else "web_only"
    print(f"\n[info] Source mode: {source_mode} "
          f"| Raindrop anchors: {n_rain} | Web fill-ins: {len(web_fill_items)}")

    # Attach cross-verification sources (from the external pool) to every anchor
    anchor_url_set = {a.get("url") or a.get("title") for a in anchor_items}
    verify_pool = dedupe_source_list(
        [x for x in external_items if (x.get("url") or x.get("title")) not in anchor_url_set]
        + external_items
    )
    anchor_items = attach_cross_verification(anchor_items, verify_pool, per_anchor=2)

    # Full source list passed to Claude (anchors + all web context for breadth)
    sources = dedupe_source_list(list(anchor_items) + external_items)

    if not sources:
        print("[error] No real context available. Exiting.")
        exit(0)

    # -- 4. Generate exactly 5 connected ideas via Claude ---------------------
    print(f"\nGenerating today's connected idea pack (x{IDEAS_PER_DAY}) "
          f"[mode={source_mode}]...")
    raw = generate_daily_connected_ideas(
        sources, ideas_per_day=IDEAS_PER_DAY, source_mode=source_mode
    )

    used_fallback = False
    if not raw and FALLBACK_ON_LLM_FAILURE:
        used_fallback = True
        print("[warn] Using fallback idea generator (FALLBACK_ON_LLM_FAILURE=1).")
        raw = fallback_connected_ideas(sources, ideas_per_day=IDEAS_PER_DAY)

    all_ideas_structured = parse_and_filter_ideas(raw)
    all_ideas_structured = all_ideas_structured[:IDEAS_PER_DAY]
    print(f"\nTotal ideas after filtering: {len(all_ideas_structured)} "
          f"(target {IDEAS_PER_DAY})")

    # Enforce exactly 5 ideas on real runs; don't consume bookmarks on failure
    if len(all_ideas_structured) != IDEAS_PER_DAY and not used_fallback:
        print("[error] Did not get exactly 5 valid ideas. "
              "Exiting -- nothing written, no bookmarks consumed.")
        exit(1)

    if not all_ideas_structured:
        print("[error] No ideas passed the quality filter. Exiting.")
        exit(0)

    if used_fallback:
        print("[warn] Fallback output is for debugging only. "
              "Skipping Google Doc write, log write, and bookmark consumption.")
        exit(1)

    # -- 5. Write to Google Docs ----------------------------------------------
    ideas_doc_text = format_ideas_for_doc(all_ideas_structured)
    if ideas_doc_text:
        append_to_google_doc([ideas_doc_text], GOOGLE_DOC_ID, "Ideas Doc", "Ideas")

    # -- 6. Save logs + mark ONLY Raindrop IDs as used ------------------------
    save_to_logs(all_ideas_structured, all_posts=[])
    for bm_id in used_ids:
        mark_bookmark_used(bm_id)
    print(f"[ok] Marked {len(used_ids)} Raindrop bookmark(s) as used.")

    print("\nCompleted VITTI Daily Ideas Pack!")