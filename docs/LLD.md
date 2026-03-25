# Low-Level Design (LLD)

## 1. Python Generation Modules

### `generate_ceo_posts.py` (CEO Post Generator)
- **`fetch_latest_financial_news()`:** Forces a strict JSON-array extraction pattern via Perplexity by demanding structured keys (`headline`, `facts`, `relevance`). It uses dynamic Regex `re.search(r'\[.*\]', content)` to scrape away Markdown wrappers like ````json`.
- **`generate_ceo_linkedin_post()`:** Implements a heavily human-centric prompt targeting the "Shubham Goyal / VITTI Capital" persona. Removes standard AI asterisks `**` or bracket arrays `[1]` post-generation to ensure authentic formatting.

### `generate_raindrop_posts.py` (Raindrop Ideas Generator)
- **`get_used_bookmarks()` / `mark_bookmark_used()`:** A unified caching safety net relying on `used_bookmarks.txt` to store String ID hashes preventing duplicate Raindrop pulls.
- **`fetch_raindrop_bookmarks()`:** Pulls the last 50 bookmarks natively via standard bearer authorization and evaluates them against the `used_bookmarks.txt` cache array to break off at exactly 5 items.
- **`fetch_web_ideas(needed_count)`:** A dynamic fallback method instantiated if Raindrop returns `< 5` new bookmarks. Uses Perplexity to seek trailing tech internet topics to ensure the daily quota of 5 generating posts always matches.

## 2. GitHub Actions Integration

### `generate.yml`
- Binds to `schedule` (`cron: 0 9 * * *`) and `workflow_dispatch` event types.
- Extracts heavily constrained Secrets (e.g. `GOOGLE_CREDENTIALS`, `PERPLEXITY_API_KEY`) and forcefully exports them into the Runner's localized OS environment using the `env:` tag.
- Pipes the string literal of `GOOGLE_CREDENTIALS` into an ad-hoc `.json` file constructed identically matches the Python script config expectations.
- Traps errors using `continue-on-error: true` so the Action doesn't paralyze both scripts if one fails.

## 3. Next.js Interaction Matrix

### `src/app/api/cache/route.js`
- Escapes the `/web` contextual scope utilizing Node's native `path.join(process.cwd(), '..', 'logs')`.
- Iterates synchronously over `fs.readdirSync`, filtering by String `endswith` mapping to specific tags (`-ceo.json`, `-raindrop.json`).
- Automatically reverse sorts and parses the latest chunk representation into memory to immediately inject into React prop-state.

### `src/app/api/trigger/route.js`
- Accepts incoming frontend POST triggers.
- Leverages the modern `fetch` library paired natively against the `api.github.com/repos/OWNER/REPO/...` structural bounds.
- Verifies and authenticates as a developer App using the header logic `Authorization: token GITHUB_PAT` alongside the strictly constrained payload `{ "ref": "main" }`.
