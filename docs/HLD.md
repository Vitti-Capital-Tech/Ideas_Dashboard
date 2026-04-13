# High-Level Design (HLD)

## 1. Purpose

The **Vitti Ideas Engine** produces **up to five independent content ideas per weekday** for professional LinkedIn-style publishing. Ideas are grounded in **multiple sources**: Raindrop bookmarks saved in the last 5 days (pinned preferred) and live **finance + tech** headlines from RSS. A single language-model pass turns that bundle into structured output (playbook + draft text), then persists it to **JSON logs** and optionally one **Google Doc**.

## 2. Design principles

| Principle | Meaning |
|-----------|---------|
| **Recency-first** | Raindrop items must have been saved within the last **5 days**; older bookmarks are ignored regardless of pin status. |
| **Pinned preference** | Within the qualifying recent items, pinned (`important=True`) items are picked first; non-pinned recents fill remaining slots. |
| **One anchor → one idea** | Each anchor source (Raindrop article or web story) maps to exactly one independently themed idea. The same anchor is never reused as the primary source for two ideas. |
| **Hybrid fill-up** | If Raindrop provides fewer than 5 qualifying items, web RSS stories fill the deficit so exactly 5 anchors are always sent to Claude. |
| **No reuse spam** | Only consumed **Raindrop** IDs are appended to `web/used_bookmarks.txt`. Web fill-ins are never marked as used. |
| **Resilient outputs** | Instead of a hard failure if 5 perfect ideas aren't found, the system uses a tiered approach (High Quality → Generic → Minimal) to reach the 5-idea target. |
| **Today-aware dashboard** | The dashboard always checks today's date first. If no log exists for today, it shows a "pending" banner and displays the most recent past ideas below it. |

## 3. Major components

1. **Source layer**
   - **Raindrop REST API:** fetch last 50 bookmarks (sorted newest first); filter for last 5 days; split into pinned + recent; cap at 5 total (pinned first).
   - **RSS aggregation:** separate finance and tech query feeds (Australia + global mix).
   - **Hybrid fill-up:** if Raindrop yields _N_ < 5 items, `pick_diverse_web_anchors` selects `5 - N` diverse web stories to fill the gap.
   - **Cross-verification:** each anchor row gets 1-2 related rows from the external pool (token overlap + fallback diversity).

2. **Generation layer**
   - **Anthropic Claude:** one request per day with separated `ANCHORS` JSON and `ADDITIONAL CONTEXT` pool.
   - **Prompt model:** "one idea per anchor, in order, independently themed" — anchor 1 → idea 1, anchor 2 → idea 2, etc.
   - **Modes:** `raindrop_plus_web` when any Raindrop items are used; `web_only` when all 5 slots are filled by web.

3. **Persistence layer**
   - **Logs:** `web/logs/YYYY-MM-DD.json` — append-only array of daily `{ timestamp, ideas }` entries.
   - **Used bookmarks:** only Raindrop IDs from the current run are appended to `web/used_bookmarks.txt`.
   - **Google Docs:** prepend human-readable block to `IDEAS_DOC_ID` when credentials exist (optional).

4. **Presentation layer (Next.js)**
   - **GET `/api/cache`:** today's date is always checked first. If today has no log, returns `ideas: null` + `previousIdeas` (most recent past log) + `previousDate`. Today is always injected into `availableDates` even if no log file exists for it yet.
   - **Dashboard:** renders a "today pending" banner when `ideas` is null; shows previous ideas below as context. Date picker labels only the real current date as "Today". Lightbulb popover uses opaque background to prevent bleed-through.

5. **Orchestration (GitHub Actions)**
   - Cron + `workflow_dispatch`; runs Python, writes artifacts, commits `web/logs` and `used_bookmarks.txt`.

## 4. End-to-end flow

```text
[Cron or manual GitHub Actions dispatch]
        │
        ▼
┌────────────────────────┐
│ Fetch Raindrop         │── last 5 days, pinned first (0-5 items)
│ + Finance RSS (14)     │
│ + Tech RSS (12)        │
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ Hybrid fill-up         │── pick_diverse_web_anchors() fills gap to 5
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ Attach cross-verify    │── per-anchor 1-2 related web items
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐
│ Claude (single call)   │── 5 ideas, one per anchor, independently themed
└──────────┬─────────────┘
           │
           ▼
┌────────────────────────┐     ┌────────────────────┐
│ Tiered Filter / Parse  │────►│ Exit without write │
│ (up to 5 ideas)        │     │ if zero candidates │
└──────────┬─────────────┘     └────────────────────┘
           │ success
           ▼
┌────────────────────────┐     ┌───────────────────┐
│ web/logs/DATE.json     │     │ Google Doc (opt.) │
│ + used_bookmarks.txt   │     │ IDEAS_DOC_ID      │
│  (Raindrop IDs only)   │     └───────────────────┘
└────────────────────────┘
           │
           ▼
   [Dashboard reads today's log — or shows previous + pending banner]
```

## 5. Logical building blocks

- **Raindrop-first, web-fallback:** Raindrop articles from the last 5 days are the preferred anchors. When there are fewer than 5, web stories fill the remainder.
- **One-anchor-one-idea:** Claude receives a numbered ANCHORS array and must generate exactly one idea per anchor in order, each independently themed.
- **Cross-verify bundle:** structured JSON passed to Claude so every anchor has peer stories for validation.
- **LinkedIn playbook:** structured fields (format name, hook, sections, CTA, why format works) plus `content.pages[].markdown` as the post draft.
- **Today-aware API:** `/api/cache` always pins today as the default date; if no log exists, it returns the previous day's ideas as a "meanwhile" fallback.

## 6. Out of scope (current)

- Pinned-only filtering (removed: all recents now qualify).
- Run Pipeline button in dashboard (removed: use GitHub Actions directly).
- CEO / separate LinkedIn pipeline, multiple Google Docs.
- Full browser rendering or paywalled article extraction (RSS + light optional URL fetch only).
