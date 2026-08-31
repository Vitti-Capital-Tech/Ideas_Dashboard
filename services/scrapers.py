import json
import re
import time
import requests

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import ASX_EQUITY_MARKET_URL


def _create_chrome_driver(headless_arg: str = "--headless"):
    options = Options()
    options.add_argument(headless_arg)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def _parse_sector_label(label_text: str):
    parts = re.findall(r">([^<]+)<", label_text)
    if len(parts) < 2:
        return None
    change = parts[0].strip()
    sector = " ".join(parts[1:]).strip()
    return {"sector": sector, "change": change}


def get_metal_prices():
    """
    Fetches metal prices in AUD and the AUD/USD FX rate using yfinance.
    Uses Yahoo Finance futures tickers for Gold, Silver, Platinum, and Palladium
    (in USD) and converts to AUD using the live AUDUSD=X rate.
    """
    import yfinance as yf

    # Yahoo Finance tickers for metal futures (USD per troy oz) and FX
    tickers = {
        "Gold": "GC=F",
        "Silver": "SI=F",
        "Platinum": "PL=F",
        "Palladium": "PA=F",
    }
    fx_ticker = "AUDUSD=X"

    metals = {}
    try:
        # Fetch AUD/USD exchange rate
        fx_data = yf.Ticker(fx_ticker)
        fx_hist = fx_data.history(period="1d")
        if fx_hist.empty:
            print("[WARN] Could not fetch AUDUSD=X rate from yfinance")
            audusd_rate = None
        else:
            audusd_rate = float(fx_hist["Close"].iloc[-1])

        for metal_name, ticker in tickers.items():
            try:
                t = yf.Ticker(ticker)
                hist = t.history(period="1d")
                if hist.empty:
                    print(f"[WARN] No data for {metal_name} ({ticker})")
                    continue
                price_usd = float(hist["Close"].iloc[-1])

                if audusd_rate and audusd_rate > 0:
                    price_aud = price_usd / audusd_rate
                    metals[metal_name] = {
                        "price": f"{price_aud:,.2f}/oz",
                        "currency": "AUD",
                    }
                else:
                    # Fallback: report in USD if FX unavailable
                    metals[metal_name] = {
                        "price": f"{price_usd:,.2f}/oz",
                        "currency": "USD",
                    }
            except Exception as metal_err:
                print(f"[WARN] Failed to fetch {metal_name}: {metal_err}")

        # FX rate (expressed as USD per 1 AUD, i.e. AUDUSD)
        if audusd_rate:
            metals["FX RATE"] = f"{audusd_rate:.4f}"
        else:
            metals["FX RATE"] = "N/A"

        print("[SUCCESS] Fetched metal prices via yfinance")

    except Exception as e:
        print(f"[ERROR] yfinance metal prices fetch failed: {e}")
        metals["FX RATE"] = "N/A"

    return metals


def get_asx_market_overview():
    """
    Fetches the daily ASX market overview, top gainers/decliners, and sector performance.
    Tries the direct JSON/SVG APIs first for speed and reliability, falling back to Selenium.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Origin": "https://www.asx.com.au",
        "Referer": "https://www.asx.com.au/"
    }
    
    # 1. API-based Fetch Attempt
    try:
        data = {}
        
        # A. Market Overview (Smart Text)
        url_markets = "https://cdn-api.markitdigital.com/apiman-gateway/ASX/asx-research/1.0/home/markets?days=1&isBoldSmartText=true"
        r = requests.get(url_markets, headers=headers, timeout=10)
        r.raise_for_status()
        markets_json = r.json()
        raw_text = markets_json.get("data", {}).get("smartText", "")
        # Strip HTML tags like <b> to match the Selenium .text property
        clean_text = re.sub(r"<[^>]+>", "", raw_text).strip()
        data["market_overview"] = clean_text if clean_text else None
        
        # B. Top 5 Gainers and Decliners
        top5_data = {"gains": [], "declines": []}
        url_top5 = "https://asx.api.markitdigital.com/asx-research/1.0/home/top-five?rows=10"
        r = requests.get(url_top5, headers=headers, timeout=10)
        r.raise_for_status()
        top5_json = r.json()
        
        # Gainers
        for item in top5_json.get("data", {}).get("gainers", [])[:5]:
            val = item.get("value", 0)
            chg = item.get("Todaychange", 0)
            last_p = item.get("lastPrice", 0)
            top5_data["gains"].append({
                "ticker": item.get("symbol", ""),
                "name": item.get("displayName", ""),
                "last_price": f"{last_p:.3f}" if isinstance(last_p, (int, float)) else str(last_p),
                "change_dollar": f"{chg:.3f}" if isinstance(chg, (int, float)) else str(chg),
                "change_pct": f"{val:.3f}%" if isinstance(val, (int, float)) else str(val)
            })
            
        # Declines
        for item in top5_json.get("data", {}).get("declines", [])[:5]:
            val = item.get("value", 0)
            chg = item.get("Todaychange", 0)
            last_p = item.get("lastPrice", 0)
            top5_data["declines"].append({
                "ticker": item.get("symbol", ""),
                "name": item.get("displayName", ""),
                "last_price": f"{last_p:.3f}" if isinstance(last_p, (int, float)) else str(last_p),
                "change_dollar": f"{chg:.3f}" if isinstance(chg, (int, float)) else str(chg),
                "change_pct": f"{val:.3f}%" if isinstance(val, (int, float)) else str(val)
            })
        data["top5_asx200"] = top5_data
        
        # C. Sectors Heatmap
        sectors = []
        url_sectors = "https://cdn-api.markitdigital.com/apiman-gateway/ASX/asx-research/1.0/home/sectors?days=1&height=450&width=780"
        r = requests.get(url_sectors, headers=headers, timeout=10)
        r.raise_for_status()
        sectors_json = r.json()
        chart_svg = sectors_json.get("data", {}).get("chart", "")
        
        soup = BeautifulSoup(chart_svg, "html.parser")
        rects = soup.find_all("rect", attrs={"data-json": True})
        for rect in rects:
            json_data = rect.get("data-json")
            if json_data:
                try:
                    parsed = json.loads(json_data)
                    label_text = parsed.get("Label", "")
                    sector_entry = _parse_sector_label(label_text)
                    if sector_entry:
                        sectors.append(sector_entry)
                except:
                    continue
        data["sectors"] = sectors
        
        print("[SUCCESS] Scraped ASX Data Successfully via API")
        return data
        
    except Exception as e:
        print(f"[WARN] ASX API fetch failed: {e}. Falling back to Selenium.")

    # 2. Fallback to original Selenium scraper
    driver = _create_chrome_driver(headless_arg="--headless")
    try:
        driver.get(ASX_EQUITY_MARKET_URL)
        time.sleep(5)

        data = {}
        try:
            overview_element = driver.find_element(
                By.XPATH,
                '//div[contains(@class,"col-md-4")]/h1[text()="Markets"]/following-sibling::div/p',
            )
            data["market_overview"] = overview_element.text.strip()
        except:
            data["market_overview"] = None

        top5_data = {"gains": [], "declines": []}
        try:
            tables = driver.find_elements(By.XPATH, '//table[@class="md-bootstrap-tooltip"]')
            for table in tables:
                caption = table.find_element(By.TAG_NAME, "caption").text.strip().lower()
                rows = table.find_elements(By.TAG_NAME, "tr")[1:]
                for row in rows[:5]:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if not cols:
                        continue
                    ticker = cols[0].find_element(By.CLASS_NAME, "symbolName").text.strip()
                    name = cols[0].find_element(By.CLASS_NAME, "displayTxt").text.strip()
                    last_price = cols[1].text.strip()
                    change_text = cols[2].text.strip()
                    match = re.search(r"([+-]?\d*\.?\d+)\s*\(([-+]?\d*\.?\d+%)\)", change_text)
                    change_dollar = match.group(1) if match else None
                    change_pct = match.group(2) if match else None

                    entry = {
                        "ticker": ticker,
                        "name": name,
                        "last_price": last_price,
                        "change_dollar": change_dollar,
                        "change_pct": change_pct,
                    }
                    if "gains" in caption:
                        top5_data["gains"].append(entry)
                    elif "declines" in caption:
                        top5_data["declines"].append(entry)
            data["top5_asx200"] = top5_data
        except:
            data["top5_asx200"] = {"gains": [], "declines": []}

        sectors = []
        try:
            rects = driver.find_elements(
                By.XPATH,
                '//section//*[local-name()="svg"]//*[local-name()="rect"][@data-json]',
            )
            for rect in rects:
                json_data = rect.get_attribute("data-json")
                if json_data:
                    try:
                        parsed = json.loads(json_data)
                        label_text = parsed.get("Label", "")
                        sector_entry = _parse_sector_label(label_text)
                        if sector_entry:
                            sectors.append(sector_entry)
                    except:
                        continue
            data["sectors"] = sectors
        except:
            data["sectors"] = []

        print("[SUCCESS] Scraped ASX Data Successfully via Selenium Fallback")
        return data
    finally:
        driver.quit()


def get_asx_monthly_overview():
    """
    Fetches the monthly ASX market overview and sector performance.
    Tries the direct JSON/SVG APIs first for speed and reliability, falling back to Selenium.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Origin": "https://www.asx.com.au",
        "Referer": "https://www.asx.com.au/"
    }
    
    # 1. API-based Fetch Attempt
    try:
        data = {}
        
        # A. Monthly Market Overview (Smart Text with days=30)
        url_markets = "https://cdn-api.markitdigital.com/apiman-gateway/ASX/asx-research/1.0/home/markets?days=30&isBoldSmartText=true"
        r = requests.get(url_markets, headers=headers, timeout=10)
        r.raise_for_status()
        markets_json = r.json()
        raw_text = markets_json.get("data", {}).get("smartText", "")
        clean_text = re.sub(r"<[^>]+>", "", raw_text).strip()
        data["market_overview"] = clean_text if clean_text else None
        
        # B. Monthly Sectors Heatmap (days=30)
        sectors = []
        url_sectors = "https://cdn-api.markitdigital.com/apiman-gateway/ASX/asx-research/1.0/home/sectors?days=30&height=450&width=780"
        r = requests.get(url_sectors, headers=headers, timeout=10)
        r.raise_for_status()
        sectors_json = r.json()
        chart_svg = sectors_json.get("data", {}).get("chart", "")
        
        soup = BeautifulSoup(chart_svg, "html.parser")
        rects = soup.find_all("rect", attrs={"data-json": True})
        for rect in rects:
            json_data = rect.get("data-json")
            if json_data:
                try:
                    parsed = json.loads(json_data)
                    label_text = parsed.get("Label", "")
                    sector_entry = _parse_sector_label(label_text)
                    if sector_entry:
                        sectors.append(sector_entry)
                except:
                    continue
        data["sectors"] = sectors
        
        print("[SUCCESS] Scraped ASX Monthly Data Successfully via API")
        return data
        
    except Exception as e:
        print(f"[WARN] ASX Monthly API fetch failed: {e}. Falling back to Selenium.")

    # 2. Fallback to original Selenium scraper
    driver = _create_chrome_driver(headless_arg="--headless=new")
    wait = WebDriverWait(driver, 20)
    data = {}

    try:
        driver.get(ASX_EQUITY_MARKET_URL)
        time.sleep(5)

        try:
            accept_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Accept')]"))
            )
            accept_btn.click()
            time.sleep(2)
            print("[INFO] Accepted cookie/privacy modal")
        except:
            print("[INFO] No cookie/privacy modal detected")

        def set_dropdown(dropdown_element, value):
            driver.execute_script(
                """
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('change'));
            """,
                dropdown_element,
                value,
            )
            time.sleep(5)

        try:
            market_dropdown = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.actions.price-days select.mk-sm")
                )
            )
            set_dropdown(market_dropdown, "30")

            overview_element = wait.until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//div[contains(@class,"col-md-4")]/h1[text()="Markets"]/following-sibling::div/p',
                    )
                )
            )
            data["market_overview"] = overview_element.text.strip()
            print("[INFO] Market Overview fetched")
        except Exception as e:
            print("[ERROR] Market Overview error:", e)
            data["market_overview"] = None

        try:
            sectors_dropdown = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.col-md-6.price-days select.mk-sm")
                )
            )
            set_dropdown(sectors_dropdown, "2")

            rects = []
            for _ in range(8):
                rects = driver.find_elements(
                    By.XPATH,
                    '//section//*[local-name()="svg"]//*[local-name()="rect"][@data-json]',
                )
                if rects:
                    break
                time.sleep(5)

            sectors = []
            for rect in rects:
                json_data = rect.get_attribute("data-json")
                if json_data:
                    try:
                        parsed = json.loads(json_data)
                        label_text = parsed.get("Label", "")
                        sector_entry = _parse_sector_label(label_text)
                        if sector_entry:
                            sectors.append(sector_entry)
                    except:
                        continue

            data["sectors"] = sectors
            print(f"[INFO] {len(sectors)} sectors fetched for 1 Month")
        except Exception as e:
            print("[ERROR] Sectors Heatmap error:", e)
            data["sectors"] = []

        print("[SUCCESS] Scraped ASX Monthly Data Successfully via Selenium Fallback")
        return data
    finally:
        driver.quit()
