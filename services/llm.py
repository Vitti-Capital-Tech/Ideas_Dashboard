import time

import requests

from config import ANTHROPIC_API_KEY, ANTHROPIC_API_URL, ANTHROPIC_MODEL, GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL


def request_groq(
    prompt: dict[str, str],
    temperature: float,
    max_tokens: int,
    retries: int = 0,
    retry_delay_sec: int = 20,
) -> str:
    """
    Fallback: Request text from Groq API.

    Used when Anthropic fails with 401/403 (auth/permission errors).
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt.get("user_prompt", "")}],
        "system": prompt.get("system_prompt", ""),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    attempts = max(1, retries + 1)
    for attempt_idx in range(attempts):
        try:
            response = requests.post(GROQ_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                if content or attempt_idx == attempts - 1:
                    return content
                print(f"ℹ️ Groq returned empty content. Retrying ({attempt_idx + 1}/{attempts})...")
            else:
                print(f"❌ Groq API Error {response.status_code}: {response.text}")
                if response.status_code in (401, 403):
                    print("❌ Groq auth failed. No further fallback available.")
                    break
                if attempt_idx == attempts - 1:
                    break

        except requests.exceptions.RequestException as e:
            print(f"❌ Groq request exception: {e}")
            if attempt_idx == attempts - 1:
                break

        if attempt_idx < attempts - 1:
            sleep_s = retry_delay_sec * (2 ** attempt_idx)
            time.sleep(sleep_s)

    return ""


def request_anthropic(
    prompt: dict[str, str],
    temperature: float,
    max_tokens: int,
    retries: int = 0,
    retry_delay_sec: int = 20,
) -> str:
    """
    Request text from Anthropic Claude.

    Retries are used when the API call succeeds but returns empty content, or for
    transient failures (e.g., 429/5xx). For 401/403 we fail fast and fall back
    to Groq.
    """
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": ANTHROPIC_MODEL,
        "messages": [{"role": "user", "content": prompt.get("user_prompt", "")}],
        "temperature": temperature,
        "system": prompt.get("system_prompt", ""),
        "max_tokens": max_tokens,
    }

    attempts = max(1, retries + 1)
    for attempt_idx in range(attempts):
        try:
            response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [{}])[0].get("text", "").strip()
                if content or attempt_idx == attempts - 1:
                    return content
                print(f"ℹ️ Anthropic returned empty content. Retrying ({attempt_idx + 1}/{attempts})...")
            else:
                print(f"❌ Anthropic API Error {response.status_code}: {response.text}")
                if response.status_code in (401, 403):
                    print("⚠️ Anthropic auth failed. Falling back to Groq...")
                    return request_groq(
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        retries=retries,
                        retry_delay_sec=retry_delay_sec,
                    )
                if attempt_idx == attempts - 1:
                    break

        except requests.exceptions.RequestException as e:
            print(f"❌ Anthropic request exception: {e}")
            if attempt_idx == attempts - 1:
                break

        if attempt_idx < attempts - 1:
            sleep_s = retry_delay_sec * (2 ** attempt_idx)
            time.sleep(sleep_s)

    return ""