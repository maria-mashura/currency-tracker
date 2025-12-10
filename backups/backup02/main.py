import requests
from bs4 import BeautifulSoup
import sqlite3
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

import logging

logging.basicConfig(
    filename="currency_errors.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def log_error(msg, e):
    logging.error(f"{msg}: {e}")


# --- 1. DB ---
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

# --- 2. BANKS ---

def fetch_privatbank():
    url = "https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5"
    try:
        data = requests.get(url).json()
        out = []
        for item in data:
            out.append({
                "bank": "PrivatBank",
                "currency": item["ccy"],
                "buy": float(item["buy"]),
                "sell": float(item["sale"]),
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        return out
    except Exception as e:
        log_error("PrivatBank fetch error:", e)
        return []


def fetch_monobank():
    url = "https://api.monobank.ua/bank/currency"
    try:
        data = requests.get(url).json()
        out = []
        for item in data:
            code = item.get("currencyCodeA")
            # 840 USD, 978 EUR, 980 UAH
            if code in (840, 978):
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
        log_error("Monobank fetch error:", e)
        return []


def fetch_oschadbank():
    url = "https://api.oschadbank.ua/open/currency"
    try:
        data = requests.get(url).json()
        out = []
        for item in data:
            currency = item.get("ccy")  # "USD", "EUR", etc.
            buy = float(item.get("buy") or 0)
            sell = float(item.get("sale") or 0)
            out.append({
                "bank": "Oschadbank",
                "currency": currency,
                "buy": buy,
                "sell": sell,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        return out
    except Exception as e:
        log_error("Oschadbank fetch error", e)
        return []


def fetch_pumb():
    url = "https://about.pumb.ua/info/currency_converter"  # источник с курсами PUMB :contentReference[oaicite:4]{index=4}
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        out = []
        table = soup.find("table")
        if not table:
            return []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
            currency = cols[0].text.strip()
            try:
                buy = float(cols[1].text.strip().replace(",", "."))
                sell = float(cols[2].text.strip().replace(",", "."))
            except:
                continue
            out.append({
                "bank": "PUMB",
                "currency": currency,
                "buy": buy,
                "sell": sell,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        return out
    except Exception as e:
        log_error("PUMB fetch error:", e)
        return []


import re
import json

def fetch_raiffeisen():
    url = "https://raiffeisen.ua/currency"
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        out = []

        # ищем JSON внутри <script> с курсами
        script = soup.find("script", string=re.compile("exchangeRates"))

        if not script:
            return []

        match = re.search(r"exchangeRates\s*=\s*(\[\{.*\}\]);", script.string)
        if not match:
            return []

        rates = json.loads(match.group(1))
        for rate in rates:
            currency = rate.get("ccy")
            buy = float(rate.get("buy") or 0)
            sell = float(rate.get("sell") or 0)
            out.append({
                "bank": "Raiffeisen Bank Ukraine",
                "currency": currency,
                "buy": buy,
                "sell": sell,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        return out
    except Exception as e:
        log_error("Raiffeisen fetch error", e)
        return []



# --- 3. SAVE ---
# --- 3. SAVE ---
def clean_bank_name(name):
    return name.replace("\u202f", "").strip()  # удаляем неразрывные пробелы

def save_rates(rates):
    for r in rates:
        cursor.execute('''
        INSERT INTO exchange_rates (bank, currency, buy, sell, date) VALUES (?, ?, ?, ?, ?)
        ''', (
            clean_bank_name(r["bank"]),  # <-- чистим название банка здесь
            r["currency"],
            r["buy"],
            r["sell"],
            r["date"]
        ))
    conn.commit()


# --- 4. COLLECT ---
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


# --- 5. API ---
app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
\

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


# --- 6. Scheduler ---
scheduler = BackgroundScheduler()
scheduler.add_job(collect_all, 'cron', hour=6)
scheduler.start()
collect_all()
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
