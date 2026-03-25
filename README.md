# Raindrop & CEO Content Generator

An incredibly polished, fully automated AI content pipeline powered by **GitHub Actions** and **Perplexity AI**, featuring a beautiful **Next.js** remote-control dashboard. 

This repository systematically turns your Raindrop.io bookmarks and trending Australian financial news into premium, human-sounding LinkedIn posts and syncs them automatically to your Google Docs.

## Key Features

- **Automagic Daily Execution**: A GitHub Actions workflow (`generate.yml`) runs the Python generation scripts at 9:00 AM UTC every single day. No servers to maintain!
- **Premium Remote Control Dashboard**: Built with Next.js, Glassmorphism CSS, and beautiful micro-animations. It acts as your viewer and manual trigger remote.
- **Smart Queueing**: The `generate_raindrop_posts.py` parser tracks `used_bookmarks.txt` to guarantee it never generates duplicates. If you bookmark fewer than 5 ideas, it seamlessly supplements the gap by searching the web for trending tech/startup insights!
- **Top-Tier "Human" AI Persona**: Strict prompt constraints prevent the Perplexity `sonar-pro` model from sounding like a corporate robot. It writes catchy, deeply insightful content built to farm engagement.
- **Effortless One-Click Copy & Post**: The Web App lets you effortlessly copy the text or jump directly into the LinkedIn Feed post modal with a single click.

## Local Setup & Dashboard Installation

If you want to run the viewer dashboard locally:

1. Clone the repository and navigate to the `web` folder.
```bash
cd web
npm install
```

2. Create a `web/.env.local` file and add your GitHub credentials to enable the manual "Trigger Workflow" button:
```ini
GITHUB_PAT=your_github_classic_token_here
GITHUB_REPO=your_username/your_repo_name
```

3. Run the development server!
```bash
npm run dev
# Open http://localhost:3000
```

## GitHub Setup (The Cloud Engine)

Because generation relies heavily on GitHub Actions, you **must** configure these exact Repository Secrets in GitHub (`Settings > Secrets and variables > Actions`):

- `PERPLEXITY_API_KEY` (Your Perplexity key)
- `RAINDROP_TOKEN` (Your Raindrop integration token)
- `GOOGLE_CREDENTIALS` (The raw JSON string of your Google Service Account)
- `CEO_LINKEDIN_DOC_ID`
- `IDEAS_DOC_ID`
- `LINKEDIN_POSTS_DOC_ID`

## Technical Documentation

Curious about how the Python and Next.js layers communicate? We have documented the architecture deeply:
- [High-Level Design (HLD)](docs/HLD.md)
- [Low-Level Design (LLD)](docs/LLD.md)

---
*Created by [Tushar Bhardwaj]*