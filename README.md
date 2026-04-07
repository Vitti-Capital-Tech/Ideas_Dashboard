# Vitti Ideas Engine

**A daily assistant that turns saved articles and live market news into five ready-to-use LinkedIn-style content ideas**—with sources checked against each other so ideas are not built from a single headline.

Built for **Vitti Capital**. The system runs on a schedule, saves results where your team can read them, and optionally syncs to one Google Doc.

---

## What this does (simple)

1. **Collects inputs**
   - **First:** any **Raindrop** bookmarks saved in the **last 5 days** that haven't been used before. Pinned (starred) items are picked first, then other recent saves. Up to 5 items are picked.
   - **Always:** recent **finance** and **tech** headlines from the web (via news feeds). Used to **cross-check** Raindrop stories—or, if Raindrop has nothing new this week, to fill all five slots from the web.

2. **Creates five independent ideas for the day**
   - A smart model (**Claude**, from Anthropic) writes **one dedicated idea per source**. If you saved 2 articles in Raindrop, those become Idea 1 and Idea 2; the remaining 3 slots are filled by distinct web stories. Each idea includes structure for LinkedIn (hook, why it matters, angle, call to action) and a **draft** you can copy.

3. **Saves outputs**
   - **Log file:** one file per day, e.g. `web/logs/2026-04-07.json`, read by your **dashboard** website.
   - **Google Doc (optional):** the same ideas can be **prepended** into one Ideas document for archiving or editing.

**You do not need to be technical** to understand the flow: save articles in Raindrop (they'll be picked up within 5 days), let the job run, then open the dashboard and use the drafts.

---

## What you get each day

| Output | What it is |
|--------|------------|
| **Five ideas** | Each anchored to its own source — Raindrop articles come first, web stories fill the rest. |
| **Cross-checking** | Every idea is validated against an independent web source (confirms, contradicts, or sharpens the angle). |
| **LinkedIn-minded structure** | Each idea has a playbook (hook, why it matters, unique take, CTA) plus a **markdown draft** ready to post. |
| **No duplicate Raindrop use** | Used bookmark IDs are stored so the same article is never reused automatically. |

---

## How it runs

```text
Scheduled time (or manual GitHub Actions trigger)
    → Fetch Raindrop (last 5 days, pinned first) + web feeds
    → Fill any gap with diverse web anchors (to always reach 5)
    → Cross-verify each anchor with 1-2 independent web items
    → Claude writes 5 ideas (one per anchor, independently themed)
    → Save JSON log + update Google Doc (if configured)
    → Mark only Raindrop bookmark IDs as used
    → Dashboard reads the latest log
```

For a **technical diagram** and terms, see [docs/HLD.md](docs/HLD.md). For **functions, files, and data shape**, see [docs/LLD.md](docs/LLD.md).

---

## Who does what

| Piece | Role |
|-------|------|
| **Raindrop** | Your article library; any bookmark saved in the last 5 days qualifies (pinned items are preferred). |
| **Web feeds** | Live finance and tech headlines — fill gaps when Raindrop has fewer than 5 new items, and always used for cross-verification. |
| **Claude** | Writes one independent idea per anchor; independently themed, not forced into a single narrative. |
| **GitHub Actions** | Runs the generator on a **daily schedule**; commits log files and `used_bookmarks.txt`. |
| **Next.js dashboard** | Shows today's ideas (or the most recent past ideas with a "pending" banner if today hasn't run yet). Date picker lets you browse any past date. **Copy draft** copies the post text; a **lightbulb** popover explains why a given LinkedIn format fits. |
| **Google Doc** | Optional archive of the same ideas in one document. |

---

## Minimum required keys

You only need **two** keys to run:

```env
RAINDROP_TOKEN=your_token
CLAUDE_API_KEY=sk-ant-...
```

Google Doc integration is silently skipped if credentials are absent.

---

## For technical readers

### Stack

- **Generator:** Python 3 (`generate_raindrop_posts.py`) — Raindrop API, RSS, Anthropic API, optional Google Docs API.
- **Dashboard:** Next.js app under `web/` — reads `web/logs/*.json` via `/api/cache`.
- **Automation:** `.github/workflows/generate.yml` — install deps, run generator, commit logs.

### Repository secrets (GitHub Actions)

Configure in your repo **Settings → Secrets and variables → Actions**:

- `ANTHROPIC_API_KEY` — Claude API key (or `CLAUDE_API_KEY`; both are supported).
- `ANTHROPIC_MODEL` — optional; defaults to Opus-class model in code.
- `RAINDROP_TOKEN` — Raindrop.io API token.
- `GOOGLE_CREDENTIALS` — service account JSON (optional; for Google Doc sync only).
- `IDEAS_DOC_ID` — Google Doc ID (optional; for Google Doc sync only).

### Local quick test

From the repository root:

```bash
pip install -r requirements.txt
python generate_raindrop_posts.py
```

Use a `.env` file for keys. To skip Google Doc locally, set `DISABLE_GOOGLE_DOC=1`.

### Local dashboard

```bash
cd web
npm install
npm run dev
```

---

## License / credits

Developed with care by [Tushar Bhardwaj](https://minianonlink.vercel.app/tusharbhardwaj).
