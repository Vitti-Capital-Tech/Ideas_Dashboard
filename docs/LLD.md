# Low-Level Design (LLD)

## 1. Entry point: `generate_raindrop_posts.py`

### Environment

| Variable | Purpose |
|----------|---------|
| `RAINDROP_TOKEN` | Bearer token for Raindrop API |
| `ANTHROPIC_API_KEY` or `CLAUDE_API_KEY` | Claude API (both checked) |
| `ANTHROPIC_MODEL` | Optional model id (code has a default) |
| `IDEAS_DOC_ID` | Target Google Doc (optional) |
| `GOOGLE_CREDENTIALS_JSON` | Path to service account JSON file (optional) |
| `DISABLE_GOOGLE_DOC` | If truthy, skip Doc API writes |
| `FALLBACK_ON_LLM_FAILURE` | Debug-only; skips log write and bookmark consumption |

`load_dotenv()` loads a root `.env` when present.

### Core functions

| Function | Behavior |
|----------|----------|
| `fetch_raindrop_bookmarks(within_days=5, max_items=5)` | GET last 50 raindrops sorted newest-first; skip IDs in `web/used_bookmarks.txt`; skip items older than `within_days`; split into `pinned[]` + `recent[]`; return `(pinned + recent)[:max_items]`. |
| `fetch_trending_finance_news()` / `fetch_trending_tech_news()` | Google News RSS-style URLs; dedupe by title; respect recency window. |
| `pick_diverse_web_anchors(finance, tech, count)` | Alternate between finance/tech pools + dedupe keys; used to fill gap when Raindrop returns fewer than 5 items. |
| `attach_cross_verification(anchors, external_items, per_anchor)` | Score token overlap; attach up to `per_anchor` external items to each anchor; fill from pool if weak overlap. |
| `dedupe_source_list(items)` | Dedupe by URL or title before sending to Claude. |
| `fetch_url_snippet(url)` | Optional HTML snippet for empty Raindrop excerpts (best-effort, no JS). |
| `generate_daily_connected_ideas(sources, ideas_per_day, source_mode)` | Splits sources into `anchor_items` (have `cross_verify`) and `context_pool`; sends `ANCHORS` + `ADDITIONAL CONTEXT` to Claude as two separate JSON blocks; instructs one idea per anchor in order. Returns raw Claude text. |
| `_normalize_idea_fields(idea)` | Merges `linkedin_playbook` into `context`/`angle`/`title` when needed; fixes key typos. |
| `parse_and_filter_ideas(raw)` | Single extract via `extract_first_json_array`; categorizes ideas into Tier 1 (High Quality), Tier 2 (Generic), and Tier 3 (Minimal); prioritized collection to reach `IDEAS_PER_DAY`. |
| `format_ideas_for_doc(ideas)` | Plain text for Google Doc: playbook fields, sources, draft excerpt. |
| `save_to_logs(ideas)` | Append `{ timestamp, ideas }` to `web/logs/{date}.json`. |
| `mark_bookmark_used(bm_id)` | Append Raindrop ID to `web/used_bookmarks.txt`. |
| `get_used_bookmarks()` | Return set of already-used Raindrop IDs from `web/used_bookmarks.txt`. |
| `append_to_google_doc(...)` | Prepend to Doc; respects size trim helpers; skips if disabled or missing creds. |

### Main control flow (`__main__`)

```
IDEAS_PER_DAY = 5

1. fetch_raindrop_bookmarks(within_days=5, max_items=5)
   → returns 0..5 items from the last 5 days (pinned first)

2. fetch_trending_finance_news() + fetch_trending_tech_news()
   → fail-exit if RSS is completely empty

3. Compute deficit = 5 - len(raindrop_items)
   If deficit > 0:
     → pick_diverse_web_anchors(finance, tech, count=deficit)
     → web_fill_items (NOT added to used_ids later)

4. anchor_items = raindrop_items + web_fill_items
   used_ids = [bm.id for bm in raindrop_items]   # Raindrop only
   source_mode = "raindrop_plus_web" if any Raindrop else "web_only"

5. attach_cross_verification(anchor_items, external_pool, per_anchor=2)

6. generate_daily_connected_ideas(sources, ideas_per_day=5, source_mode)
   → Claude prompt: "one idea per anchor, in order, independently themed"

7. parse_and_filter_ideas(raw)   → Resilient top-up up to 5 ideas

8. On success:
   append_to_google_doc(...)      (if enabled)
   save_to_logs(ideas)
   for bm_id in used_ids:
       mark_bookmark_used(bm_id)  (Raindrop IDs only)
```

### Prompt model (`generate_daily_connected_ideas`)

The function now separates sources into two blocks before calling Claude:

- **`anchor_items`** — sources that have a `cross_verify` array attached (these are the primary anchors, one per idea).
- **`context_pool`** — remaining sources (no `cross_verify`), passed as `ADDITIONAL CONTEXT` for enrichment only.

Claude receives the instruction: **"Anchor 1 → Idea 1, Anchor 2 → Idea 2… Each idea must have a different topic."** This prevents the old behaviour where 2 Raindrop articles would be woven into all 5 ideas as a single themed series.

### JSON extraction

`extract_first_json_array` walks bracket depth to find the first `[{...}]` or a single object, stripping ``` fences — reduces breakage from stray `[1]` footnote-style citations.

---

## 2. Next.js application (`web/`)

### `src/app/api/cache/route.js`

- Resolves `logs` dir: `process.cwd()/logs` or `process.cwd()/web/logs`.
- Computes `todayStr` = `YYYY-MM-DD` in server local time.
- **Available dates:** scan root `*.json`; always inject `todayStr` at position 0 even if no log file exists for today yet.
- **On initial load** (no `?date=` param): serve today's log. If today has no log, return `ideas: null` + `previousIdeas` (most recent past log) + `previousDate`.
- **On date change** (`?date=YYYY-MM-DD`): serve that date's log only.
- Response: `{ ideas, previousIdeas, previousDate, availableDates, selectedDate, todayStr }`.

### `src/app/page.js`

- Fetches `/api/cache`; renders **Ideas only** (Posts tab removed).
- State includes `todayStr` + `previousIdeas` + `previousDate` from API response.
- **Today pending state:** when `ideas` is null, shows a dashed purple banner ("Today's ideas haven't been generated yet") and renders `previousIdeas` cards below it.
- **Date picker:** "Today (YYYY-MM-DD)" label is applied only when the option value equals `todayStr` (not just the most recent date).
- **IdeaCard:** series strip; badges; LinkedIn playbook (hook, why, unique take, CTA, poll list); **lightbulb** toggles popover for `why_this_works`; pager draft; **Copy draft** button.
- **Lightbulb popover:** solid opaque background (`--bg-popover`) prevents content bleed-through in both dark and light themes.
- **Run Pipeline button** removed; pipeline must be triggered via GitHub Actions.

### `src/app/globals.css`

- Design tokens including `--bg-popover: #0e1a33` (dark) / `#ffffff` (light) for the lightbulb popover.
- Glass cards, pager accordion, skeleton shimmer, date pill styles.

---

## 3. Data schema (idea object)

Minimal shape stored in logs (exact fields may vary by model run):

```json
{
  "anchor_source": "url of the primary anchor for this idea",
  "title": "string",
  "context": "string",
  "angle": "string",
  "linkedin_playbook": {
    "format_name": "string",
    "opening_hook": "string",
    "why_section": "string",
    "unique_take": "string",
    "call_to_action": "string",
    "why_this_works": "string",
    "poll_options": ["optional"]
  },
  "grounding": {
    "sources_used": [
      { "source_type": "raindrop|news|tech|web", "title": "string", "url": "string" }
    ]
  },
  "region": "Australia|Global|Mixed",
  "source_type": "raindrop|news|hybrid",
  "content": {
    "format": "1-pager",
    "pages": [
      { "page_title": "Draft", "markdown": "string" }
    ]
  }
}
```

> **Note:** `series_title`, `series_thesis`, and `connections.builds_on` fields from the old series-based schema are no longer generated by the prompt. The dashboard handles their absence gracefully.

---

## 4. Files & paths

| Path | Role |
|------|------|
| `generate_raindrop_posts.py` | Daily generator |
| `web/logs/YYYY-MM-DD.json` | Dashboard input (one file per day) |
| `web/used_bookmarks.txt` | Raindrop IDs consumed (one per line) |
| `.github/workflows/generate.yml` | CI schedule + manual dispatch |
| `requirements.txt` | Python deps (`anthropic`, `requests`, Google clients, etc.) |
| `docs/HLD.md` | High-level architecture |
| `docs/LLD.md` | This file |

---

## 5. Failure behaviour

- **Claude errors / overload:** retries with backoff; if still no valid five ideas, process exits **without** writing logs or consuming bookmarks.
- **Fewer than 5 ideas returned:** The script now "rescues" generic or slightly incomplete ideas to reach the target. It only fails if zero candidates are found.
- **Empty RSS:** hard exit (cannot cross-verify; bookmarks not consumed).
- **Malformed log file:** `_load_log_file` returns `[]` and starts fresh on write.
- **No Raindrop items (last 5 days fully consumed or no new saves):** falls back to `web_only` mode automatically — no error, pipeline continues normally.
