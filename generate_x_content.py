import json
from datetime import datetime, timedelta

from config import SYDNEY_TZ, get_today_str
from services.llm import request_anthropic
from services.prompts import build_daily_prompt, build_monthly_prompt, build_morning_prompt
from services.scrapers import get_asx_market_overview, get_asx_monthly_overview, get_metal_prices
from services.twitter import parse_thread_posts, post_thread_to_x



LLM_RETRIES = 2
LLM_RETRY_DELAY_SEC = 20


def is_last_trading_day(date: datetime) -> bool:
    next_day = date + timedelta(days=1)
    if next_day.month != date.month:
        return date.weekday() < 5
    return False


def save_x_to_logs(content_type: str, content: str):
    import os
    if not content:
        return
    date_str = datetime.now(SYDNEY_TZ).strftime("%Y-%m-%d")
    os.makedirs('web/logs', exist_ok=True)
    x_file = f"web/logs/x_{date_str}.json"
    
    entry = {
        "timestamp": datetime.now(SYDNEY_TZ).isoformat(),
        "type": content_type,
        "content": content
    }
    
    existing = []
    if os.path.exists(x_file):
        try:
            with open(x_file, 'r', encoding='utf-8') as f:
                raw = f.read().strip()
                if raw:
                    existing = json.loads(raw)
                    if not isinstance(existing, list):
                        existing = [existing]
        except Exception as e:
            print(f"⚠️ Error loading existing X log: {e}")
            
    existing.append(entry)
    
    try:
        with open(x_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=4)
        print(f"[ok] X content logged to {x_file}")
    except Exception as e:
        print(f"❌ Error writing X log: {e}")


def generate_market_commentary() -> str:
    today_str = get_today_str()
    market_overview_text = get_asx_market_overview()
    market_overview_json = json.dumps(market_overview_text, indent=2)
    metals_data = get_metal_prices()
    print(metals_data)
    print(market_overview_json)
    print(today_str)
    prompt = build_daily_prompt(today_str, market_overview_text, metals_data)
    return request_anthropic(
        prompt=prompt,
        temperature=0.7,
        max_tokens=5000,
        retries=LLM_RETRIES,
        retry_delay_sec=LLM_RETRY_DELAY_SEC,
    )


def monthly_summary() -> str:
    today_str = get_today_str()
    market_overview_text = get_asx_monthly_overview()
    market_overview_json = json.dumps(market_overview_text, indent=2)
    print(market_overview_json)
    prompt = build_monthly_prompt(today_str, market_overview_text)
    res = request_anthropic(
        prompt=prompt,
        temperature=0.8,
        max_tokens=5000,
        retries=LLM_RETRIES,
        retry_delay_sec=LLM_RETRY_DELAY_SEC,
    )
    if res:
        save_x_to_logs('monthly', res)
        posts = parse_thread_posts(res)
        post_thread_to_x(posts)
    return res


def generate_morning_market_commentary() -> str:
    today_str = get_today_str()
    prompt = build_morning_prompt(today_str)
    return request_anthropic(
        prompt=prompt,
        temperature=0.7,
        max_tokens=2500,
        retries=LLM_RETRIES,
        retry_delay_sec=LLM_RETRY_DELAY_SEC,
    )


def send_morning_email():
    today_str = datetime.now(SYDNEY_TZ).strftime("%Y-%m-%d")
    commentary = generate_morning_market_commentary()
    if commentary:
        save_x_to_logs('morning', commentary)
        print(f"📧 Morning commentary sent at {datetime.now(SYDNEY_TZ)}: {commentary}")
        posts = parse_thread_posts(commentary)
        post_thread_to_x(posts)
        return commentary


def run_scheduler():
    import os
    import pytz
    today = datetime.now(SYDNEY_TZ)
    today_str = today.strftime("%Y-%m-%d")
    weekday = today.weekday()
    hour = today.hour
    
    # Check if this is a manual run via GitHub Actions UI
    is_manual = os.getenv("GITHUB_EVENT_NAME") == "workflow_dispatch"

    print(f"🕒 Sydney Local Time: {today.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Weekday: {weekday}, Hour: {hour}, Manual: {is_manual}")

    if weekday >= 5:
        print("⛔ Weekend in Sydney, skipping commentary.")
        return

    # Determine if we are in Daylight Saving Time (AEDT vs AEST)
    # AEDT is UTC+11, AEST is UTC+10
    is_dst = today.dst() != timedelta(0)
    
    # Calculate current minutes since midnight UTC
    now_utc = datetime.now(pytz.utc)
    minutes_utc = now_utc.hour * 60 + now_utc.minute

    # 1. Morning/Monthly Window (Target: 8:00 AM Sydney)
    if hour < 14:
        # The scheduler triggers twice in the morning:
        # - Trigger A: 21:15 UTC (minutes_utc = 1275) -> 08:15 AEDT / 07:15 AEST
        # - Trigger B: 22:15 UTC (minutes_utc = 1335) -> 09:15 AEDT / 08:15 AEST
        #
        # If DST is active (AEDT): we want Trigger A (minutes_utc < 1335)
        # If DST is not active (AEST): we want Trigger B (minutes_utc >= 1335)
        is_correct_trigger = (minutes_utc < 1335) if is_dst else (minutes_utc >= 1335)

        if is_correct_trigger or is_manual:
            if is_last_trading_day(today):
                print("📨 Last trading day of the month → generating monthly summary...")
                report = monthly_summary()
                if report:
                    print("Report of the last trading day:", report)
                    return report
            elif weekday == 0:
                print("🟢 Monday morning, generating pre-market commentary")
                send_morning_email()
            else:
                print("⏳ Morning trigger ignored (not Monday or Last Trading Day)")
        else:
            trigger_name = "Trigger A (21:15 UTC)" if minutes_utc < 1335 else "Trigger B (22:15 UTC)"
            season = "AEDT (DST)" if is_dst else "AEST (Standard Time)"
            print(f"⏳ Morning window: {trigger_name} is ignored during {season}.")

    # 2. Evening Window (Target: 5:00 PM Sydney / Hour 17)
    elif hour >= 15:
        # The scheduler triggers twice in the evening:
        # - Trigger A: 06:15 UTC (minutes_utc = 375) -> 17:15 AEDT / 16:15 AEST
        # - Trigger B: 07:15 UTC (minutes_utc = 435) -> 18:15 AEDT / 17:15 AEST
        #
        # If DST is active (AEDT): we want Trigger A (minutes_utc < 435)
        # If DST is not active (AEST): we want Trigger B (minutes_utc >= 435)
        is_correct_trigger = (minutes_utc < 435) if is_dst else (minutes_utc >= 435)

        if is_correct_trigger or is_manual:
            print("🟢 Evening window, generating daily commentary")
            commentary = generate_market_commentary()
            if commentary:
                save_x_to_logs('daily', commentary)
                print(f"📝 Daily commentary sent at {datetime.now(SYDNEY_TZ)}: {commentary}")
                posts = parse_thread_posts(commentary)
                post_thread_to_x(posts)
                return commentary
        else:
            trigger_name = "Trigger A (06:15 UTC)" if minutes_utc < 435 else "Trigger B (07:15 UTC)"
            season = "AEDT (DST)" if is_dst else "AEST (Standard Time)"
            print(f"⏳ Evening window: {trigger_name} is ignored during {season}.")
    
    else:
        print(f"⏳ Hour {hour} is outside of defined scheduling windows.")


if __name__ == "__main__":
    run_scheduler()
