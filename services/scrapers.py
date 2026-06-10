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
    Uses the direct AJAX feed for better reliability and explicit currency selection.
    """

    # Currency ID 2 is AUD, 1 is USD.
    aud_feed_url = f"{ABCBULLION_URL.rstrip('/')}/price/hfeeds?currency_id=2"
    
    try:
        response = requests.get(aud_feed_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        metals = {}
        # The feed returns a series of <li> elements
        for item in soup.find_all("li"):
            try:
                h5 = item.find("h5")
                p = item.find("p")
                if h5 and p:
                    title = h5.get_text(strip=True)
                    value = p.get_text(strip=True)
                    # Clean up the value (e.g., "$3,614.45/oz " -> "3,614.45/oz")
                    value = value.replace("$", "").strip()
                    metals[title] = {
                        "price": value,
                        "currency": "AUD"
                    }
            except:
                continue
        
        if metals:
            # Check for FX Rate which is usually in the last li or has a different structure
            # but in our direct feed test it was just another li.
            return metals

    except Exception as e:
        print(f"⚠️ Direct feed fetch failed: {e}. Falling back to Selenium.")

    # Fallback to Selenium if direct request fails or returns nothing
    driver = _create_chrome_driver(headless_arg="--headless")
    try:
        driver.get(ABCBULLION_URL)
        # Wait for the price element to be populated
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#hprice li h5")))
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        metals = {}
        price_list = soup.select("#hprice li")
        for item in price_list:
            try:
                title = item.find("h5").get_text(strip=True)
                value = item.find("p").get_text(strip=True).replace("$", "").strip()
                metals[title] = {
                    "price": value,
                    "currency": "AUD"
                }   
            except:
                pass

        fx = soup.select_one(".exchangeRate p a")
        fx_rate = fx.get_text(strip=True) if fx else "N/A"
        metals["FX RATE"] = fx_rate
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
