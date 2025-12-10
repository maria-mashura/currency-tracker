import requests
import sqlite3
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
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

# PrivatBank API
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
        log(f"PrivatBank: {len(out)} rates fetched")
        return out
    except Exception as e:
        log_error("PrivatBank fetch error", e)
        return []

# Monobank API
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
        log(f"Monobank: {len(out)} rates fetched")
        return out
    except Exception as e:
        log_error("Monobank fetch error", e)
        return []

# --- NBU API для остальных банков ---
NBU_BANKS = {
    "Oschadbank": "Ощадбанк",
    "PUMB": "ПУМБ",
    "Raiffeisen": "Райффайзен"
}

def fetch_nbu_bank(bank_latin_name):
    """
    Получает курс USD и EUR через API НБУ для указанного банка
    """
    try:
        url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"
        data = requests.get(url).json()
        out = []
        for item in data:
            if item["cc"] not in ("USD", "EUR"):
                continue
            out.append({
                "bank": bank_latin_name,
                "currency": item["cc"],
                "buy": float(item["rate"]),   # используем как buy
                "sell": float(item["rate"]),  # используем как sell
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        log(f"{bank_latin_name}: {len(out)} rates fetched")
        return out
    except Exception as e:
        log_error(f"{bank_latin_name} fetch error", e)
        return []

# --- Функции для конкретных банков ---
def fetch_oschadbank():
    return fetch_nbu_bank("Oschadbank")

def fetch_pumb():
    return fetch_nbu_bank("PUMB")

def fetch_raiffeisen():
    return fetch_nbu_bank("Raiffeisen")

# --- 3. SAVE ---
def save_rates(rates):
    for r in rates:
        cursor.execute('''
        INSERT INTO exchange_rates (bank, currency, buy, sell, date) VALUES (?, ?, ?, ?, ?)
        ''', (
            r['bank'], r['currency'], r['buy'], r['sell'], r['date']
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
        result.append({"bank": b, "currency": c, "buy": buy, "sell": sell, "date": date})
    return {"rates": result}

# --- 6. Scheduler ---
scheduler = BackgroundScheduler()
scheduler.add_job(collect_all, 'cron', hour=6)
scheduler.start()
collect_all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
