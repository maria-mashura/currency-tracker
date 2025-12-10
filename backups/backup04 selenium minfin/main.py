import requests
import time
import sqlite3
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import logging
from fastapi.middleware.cors import CORSMiddleware

# --- Logging ---
logging.basicConfig(
    filename="currency_debug.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def log(msg):
    logging.info(msg)
    print(msg)

def log_error(msg, e):
    logging.error(f"{msg}: {e}")


# --- DB ---
conn = sqlite3.connect("currency.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS exchange_rates(
    bank TEXT,
    currency TEXT,
    buy REAL,
    sell REAL,
    date TEXT
)
''')
conn.commit()


# --- PrivatBank ---
def fetch_privatbank():
    url = "https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5"
    try:
        data = requests.get(url).json()
        out = []
        for item in data:
            if item["ccy"] == "RUB":
                continue
            out.append({
                "bank": "PrivatBank",
                "currency": item["ccy"],
                "buy": float(item["buy"]),
                "sell": float(item["sale"]),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        return out
    except Exception as e:
        log_error("PrivatBank fetch error", e)
        return []


# --- Monobank ---
def fetch_monobank():
    url = "https://api.monobank.ua/bank/currency"
    try:
        data = requests.get(url).json()
        out = []
        for item in data:
            code = item.get("currencyCodeA")
            if code in (840, 978):  # USD / EUR
                cur = {840: "USD", 978: "EUR"}[code]
                buy = item.get("rateBuy") or item.get("rateCross") or 0
                sell = item.get("rateSell") or item.get("rateCross") or 0
                out.append({
                    "bank": "Monobank",
                    "currency": cur,
                    "buy": buy,
                    "sell": sell,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        return out
    except Exception as e:
        log_error("Monobank fetch error", e)
        return []


# --- Minfin ---
BASE_URL = "https://minfin.com.ua/ua/currency/banks/"
BANKS = ["Ощадбанк", "ПУМБ", "Райффайзен"]

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

service = Service(r"C:\Users\GuestUser\Documents\BA\Currency_project\Currency_tracker\chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)

def fetch_minfin_bank(bank_name):
    """Собирает курсы USD и EUR с Minfin для конкретного банка"""
    try:
        driver.get(BASE_URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".currency-table__row"))
        )
        time.sleep(1)

        rows = driver.find_elements(By.CSS_SELECTOR, ".currency-table__row")
        results = []

        for row in rows:
            try:
                title_el = row.find_element(By.CSS_SELECTOR, ".currency-table__title")
                title = title_el.text.strip()
                if bank_name.lower() not in title.lower():
                    continue

                cells = row.find_elements(By.CSS_SELECTOR, ".currency-table__cell")
                for i in range(0, len(cells), 3):
                    if i + 2 >= len(cells):
                        continue
                    currency = cells[i].text.strip()
                    if currency not in ("USD", "EUR"):
                        continue
                    try:
                        buy = float(cells[i+1].text.strip().replace(",", "."))
                        sell = float(cells[i+2].text.strip().replace(",", "."))
                    except ValueError:
                        continue
                    results.append({
                        "bank": bank_name,
                        "currency": currency,
                        "buy": buy,
                        "sell": sell,
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            except:
                continue

        log(f"{bank_name}: {len(results)} rates fetched")
        return results

    except TimeoutException:
        log(f"{bank_name}: timed out waiting for table to load")
        return []
    except Exception as e:
        log(f"{bank_name} fetch error: {e}")
        return []

def fetch_oschadbank():
    return fetch_minfin_bank("Ощадбанк")

def fetch_pumb():
    return fetch_minfin_bank("ПУМБ")

def fetch_raiffeisen():
    return fetch_minfin_bank("Райффайзен")


# --- Save ---
def clean_bank_name(name):
    return name.replace("\u202f", "").strip()

def save_rates(rates):
    for r in rates:
        cursor.execute('''
        INSERT INTO exchange_rates (bank, currency, buy, sell, date) VALUES (?, ?, ?, ?, ?)
        ''', (
            clean_bank_name(r["bank"]),
            r["currency"],
            r["buy"],
            r["sell"],
            r["date"]
        ))
    conn.commit()


# --- Collect ---
def collect_all():
    print("Collecting ...", datetime.now())
    all_rates = []
    all_rates += fetch_privatbank()
    all_rates += fetch_monobank()
    all_rates += fetch_oschadbank()
    all_rates += fetch_pumb()
    all_rates += fetch_raiffeisen()
    if all_rates:
        save_rates(all_rates)
        print("Saved", len(all_rates), "rates")
    else:
        print("No rates fetched")


# --- API ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/rates/latest")
def latest():
    cursor.execute('''
    SELECT bank, currency, buy, sell, date
    FROM exchange_rates
    ORDER BY date DESC
    LIMIT 100
    ''')
    rows = cursor.fetchall()
    result = []
    for b, c, buy, sell, date in rows:
        result.append({
            "bank": b,
            "currency": c,
            "buy": buy,
            "sell": sell,
            "date": date
        })
    return {"rates": result}


# --- Scheduler ---
scheduler = BackgroundScheduler()
scheduler.add_job(collect_all, 'cron', hour=6)
scheduler.start()
collect_all()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
