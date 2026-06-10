# Vitti Ideas Engine

**A weekday assistant that turns saved articles and live market news into ready-to-use LinkedIn-style content ideas**—with sources checked against each other so ideas are not built from a single headline.

Built for **Vitti Capital**. The system runs on a schedule, saves results where your team can read them, and optionally syncs to one Google Doc.

---

## What this does (simple)

1. **Collects inputs**
   - **First:** any **Raindrop** bookmarks saved in the **last 5 days** that haven't been used before. Pinned (starred) items are picked first, then other recent saves. Up to 5 items are picked.
   - **Always:** recent **finance** and **tech** headlines from the web (via news feeds). Used to **cross-check** Raindrop stories—or, if Raindrop has nothing new this week, to fill all five slots from the web.

2. **Creates five independent ideas for the day**
   - A smart model (**Claude**, from Anthropic) writes **one dedicated idea per source**. If you saved 2 articles in Raindrop, those become Idea 1 and Idea 2; the remaining 3 slots are filled by distinct web stories. Each idea includes structure for LinkedIn (hook, why it matters, angle, call to action) and a **draft** you can copy.

3. **Saves outputs**
   - **Log files:** 
     - Raindrop Ideas: e.g. `web/logs/2026-04-07.json`
     - X Content & Commentary: e.g. `web/logs/x_2026-04-07.json`
     Both are read dynamically by your **dashboard** website.
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
    → Claude writes up to 5 ideas (prioritizing high-quality, but allowing rescued tiers to reach target)
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
| **Claude / LLMs** | Writes one independent idea per anchor; also generates morning outlooks, daily closings, and monthly summaries for X. |
| **GitHub Actions** | Runs the Daily generator and the X Content scheduler on a **weekday schedule**; commits generated JSON logs to the repo. |
| **Next.js dashboard** | Shows today's ideas and X commentary (with fallbacks to previous days if today hasn't run yet). Tab-bar Navbar allows navigating between **Ideas** and **X Content** dashboards. |
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

- **Generator (Ideas):** Python 3 (`generate_raindrop_posts.py`) — Raindrop API, RSS, Anthropic API, optional Google Docs API.
- **Generator (X Content):** Python 3 (`generate_x_content.py`) — Selenium market scraper, ABC Bullion scrapers, Anthropic/Groq APIs.
- **Dashboard:** Next.js app under `web/` — reads `web/logs/*.json` via `/api/cache` and `/api/x_cache`.
- **Automation:** 
  - `.github/workflows/generate.yml` — Daily Ideas generator scheduler.
  - `.github/workflows/generate_x_content.yml` — X Content scheduler (runs 4 times/day, matching Sydney trading sessions).

### Repository secrets (GitHub Actions)

Configure in your repo **Settings → Secrets and variables → Actions**:

- `ANTHROPIC_API_KEY` — Claude/Anthropic API key.
- `GROQ_API_KEY` — Groq API key (used as fallback for X Content generation).
- `RAINDROP_TOKEN` — Raindrop.io API token.
- `GOOGLE_CREDENTIALS` — service account JSON (optional; for Google Doc sync only).
- `IDEAS_DOC_ID` — Google Doc ID (optional; for Google Doc sync only).

### Local quick test

From the repository root:

```bash
pip install -r requirements.txt

# Run daily ideas generator
python generate_raindrop_posts.py

# Run X content generator (simulating manual run to override timing check)
$env:GITHUB_EVENT_NAME="workflow_dispatch"
python generate_x_content.py
```

Use a `.env` file for keys.

### Local dashboard

```bash
cd web
npm install
npm run dev
```

---

## License / credits

Developed with care by [Tushar Bhardwaj](https://minianonlink.vercel.app/tusharbhardwaj).
