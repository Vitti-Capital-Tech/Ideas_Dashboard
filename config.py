import os
from datetime import datetime
from pathlib import Path

import pytz

# Load local .env (for local runs only)
def _load_local_env():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        # Do not override real environment variables (e.g., CI secrets).
        os.environ.setdefault(key, value)


_load_local_env()

# LLM configuration
_anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if _anthropic_api_key is None or not str(_anthropic_api_key).strip():
    # Fail fast in CI so we don't accidentally run with a stale/invalid fallback key.
    # GitHub Actions sets `GITHUB_ACTIONS=true`.
    if os.getenv("GITHUB_ACTIONS") == "true" or os.getenv("CI"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is missing/empty in CI. Check GitHub Actions secret name/value "
            "(repo Settings -> Secrets and variables -> Actions)."
        )

_groq_api_key = os.getenv("GROQ_API_KEY")
if _groq_api_key is None or not str(_groq_api_key).strip():
    # Fail fast in CI so we don't accidentally run with a stale/invalid fallback key.
    # GitHub Actions sets `GITHUB_ACTIONS=true`.
    if os.getenv("GITHUB_ACTIONS") == "true" or os.getenv("CI"):
        raise RuntimeError(
            "GROQ_API_KEY is missing/empty in CI. Check GitHub Actions secret name/value "
            "(repo Settings -> Secrets and variables -> Actions)."
        )

ANTHROPIC_API_KEY = _anthropic_api_key
ANTHROPIC_MODEL = "claude-sonnet-4-6"

GROQ_API_KEY = _groq_api_key
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"

# URLs
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ABCBULLION_URL = "https://www.abcbullion.com.au/"
ASX_EQUITY_MARKET_URL = (
    "https://www.asx.com.au/markets/trade-our-cash-market/"
    "equity-market-prices?utm_widget=topTwenty"
)

# Timezone/date helpers
SYDNEY_TZ = pytz.timezone("Australia/Sydney")

def get_today_str() -> str:
    return datetime.now(SYDNEY_TZ).strftime("%Y-%m-%d")
