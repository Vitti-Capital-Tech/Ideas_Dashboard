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

from config import ABCBULLION_URL, ASX_EQUITY_MARKET_URL


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
    Fetches metal prices in AUD from ABC Bullion.
    Uses the direct JSON API for high reliability and speed, 
    with a robust Selenium scraper as a fallback.
    """
    # 1. Direct JSON API attempt
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        aud_url = f"{ABCBULLION_URL.rstrip('/')}/api/metals/prices/aud"
        usd_url = f"{ABCBULLION_URL.rstrip('/')}/api/metals/prices/usd"
        
        response_aud = requests.get(aud_url, headers=headers, timeout=10)
        response_aud.raise_for_status()
        data_aud = response_aud.json()
        
        metals = {}
        for metal_key, api_key in [("Gold", "gold"), ("Silver", "silver"), ("Platinum", "platinum"), ("Palladium", "palladium")]:
            price_val = data_aud["prices"][api_key]["ask"]["value"]
            metals[metal_key] = {
                "price": f"{price_val:,.2f}/oz",
                "currency": "AUD"
            }
            
        # Try to get USD prices to calculate FX rate
        try:
            response_usd = requests.get(usd_url, headers=headers, timeout=10)
            response_usd.raise_for_status()
            data_usd = response_usd.json()
            gold_usd = data_usd["prices"]["gold"]["ask"]["value"]
            gold_aud = data_aud["prices"]["gold"]["ask"]["value"]
            fx_rate = round(gold_usd / gold_aud, 4)
            metals["FX RATE"] = f"{fx_rate:.4f}"
        except Exception as fx_err:
            print(f"⚠️ Could not calculate FX rate from API: {fx_err}")
            metals["FX RATE"] = "N/A"
            
        if metals:
            return metals
            
    except Exception as e:
        print(f"⚠️ Direct API fetch failed: {e}. Falling back to Selenium.")

    # 2. Fallback to Selenium
    driver = _create_chrome_driver(headless_arg="--headless")
    try:
        driver.get(ABCBULLION_URL)
        wait = WebDriverWait(driver, 15)
        # Wait for the skeleton loaders to be replaced by actual price text (3 p tags inside store/gold link)
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, 'a[href*="/store/gold"] p')) >= 3)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        metals = {}
        for metal_key, metal_name in [("Gold", "gold"), ("Silver", "silver"), ("Platinum", "platinum"), ("Palladium", "palladium")]:
            try:
                link = soup.find("a", href=lambda x: x and f"/store/{metal_name}" in x)
                if link:
                    ps = link.find_all("p")
                    if len(ps) >= 3:
                        price_val = ps[1].get_text(strip=True)
                        metals[metal_key] = {
                            "price": f"{price_val}/oz" if "/oz" not in price_val else price_val,
                            "currency": "AUD"
                        }
            except Exception as scrape_err:
                print(f"⚠️ Failed to scrape {metal_key} in Selenium fallback: {scrape_err}")
        
        # Fallback FX rate attempt using API (if it was a temporary scrape issue on AUD page)
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            usd_url = f"{ABCBULLION_URL.rstrip('/')}/api/metals/prices/usd"
            response_usd = requests.get(usd_url, headers=headers, timeout=5)
            data_usd = response_usd.json()
            gold_usd = data_usd["prices"]["gold"]["ask"]["value"]
            # Extract numerical gold price from scraped metals
            if "Gold" in metals:
                gold_aud_str = metals["Gold"]["price"].replace("/oz", "").replace(",", "").strip()
                gold_aud = float(gold_aud_str)
                fx_rate = round(gold_usd / gold_aud, 4)
                metals["FX RATE"] = f"{fx_rate:.4f}"
            else:
                metals["FX RATE"] = "N/A"
        except Exception:
            metals["FX RATE"] = "N/A"
            
        return metals
    finally:
        driver.quit()


def get_asx_market_overview():
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

        print("🟢 Scraped ASX Data Successfully")
        return data
    finally:
        driver.quit()


def get_asx_monthly_overview():
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
            print("🟢 Accepted cookie/privacy modal")
        except:
            print("ℹ️ No cookie/privacy modal detected")

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
            print("🟢 Market Overview fetched")
        except Exception as e:
            print("❌ Market Overview error:", e)
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
            print(f"🟢 {len(sectors)} sectors fetched for 1 Month")
        except Exception as e:
            print("❌ Sectors Heatmap error:", e)
            data["sectors"] = []

        print("🟢 Scraped ASX Monthly Data Successfully")
        return data
    finally:
        driver.quit()
