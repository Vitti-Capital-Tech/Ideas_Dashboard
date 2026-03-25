# High-Level Design (HLD)

## 1. Introduction

The **Content Generator** repository automates the curation and generation of LinkedIn content utilizing the Perplexity AI platform. It connects disparate data sources (Raindrop.io bookmarks and live internet news search) to generate highly professional outputs.

## 2. Core Architecture

The system operates across a **Decoupled Serverless Hierarchy**, meaning the heavy lifting of API requests and generation is fully removed from the frontend application and handed explicitly over to GitHub's continuous integration runners.

### System Components:

1. **The Generation Engine (Python Scripts)**
   - **Data Extraction**: Pulls data from Raindrop.io (`generate_raindrop_posts.py`) or natively extracts financial news using Perplexity's searching capabilities (`generate_ceo_posts.py`).
   - **Prompt Processing**: Interfaces with `sonar-pro` using strict, highly curated constraints to return human-like markdown strings.
   - **Google Docs Sync**: Authenticates via `google.oauth2.service_account` to prepend formatted text to specific Google Docs (`IDEAS_DOC`, `CEO_LINKEDIN_DOC`, `LINKEDIN_POSTS_DOC`).
   - **Log File Artifacting**: Dumps exact generation outputs as structured JSON artifacts securely inside the `/logs` directory based on the execution date.

2. **The Orchestration Layer (GitHub Actions)**
   - `.github/workflows/generate.yml`
   - Configured to execute automatically at predetermined intervals (daily cron).
   - Serves as the primary executor, downloading dependencies, consuming Repository Secrets, executing the Python Engine, and automatically pushing the generated `/logs` and `used_bookmarks.txt` via `git commit` to the master branch.

3. **The Web Dashboard (Next.js)**
   - Operates completely autonomously relying only on the GitHub Repo.
   - **Log Aggregator**: Scans the `/logs` folders (if run locally) to parse and render the most recent JSON structures into interactive React `PostCard` components.
   - **Remote Control Trigger**: Communicates with the public GitHub API utilizing a Personal Access Token (`GITHUB_PAT`) to manually trigger the `workflow_dispatch` event on the repository if the user requests an immediate generation payload.

## 3. Data Flow Execution Diagram

```text
[User] -> Opens Web Dashboard -> Web App reads `/logs/*.json` -> User views Posts.

[User] -> Clicks "Trigger Action"
   |
   +-> [Web App] -> POST req to GitHub API
         |
         +-> [GitHub Actions Workflow Starts] (or triggered automatically via Cron)
               |
               +-> Loads Python Env & GitHub Secrets
               +-> Runs `generate_ceo_posts.py` & `generate_raindrop_posts.py`
               +-> Pings Perplexity.ai
               +-> Pushes Text to Google Docs
               +-> Creates `logs/2026-XX-XX.json`
               +-> `git push` to repository -> Cycle Completes.
```
