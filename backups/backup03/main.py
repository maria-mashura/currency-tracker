import requests
from bs4 import BeautifulSoup
import sqlite3
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging

from fastapi.middleware.cors import CORSMiddleware

# --- Logging ---
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
        log_error("PrivatBank fetch error:", e)
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
        log_error("Monobank fetch error:", e)
        return []

# --- Minfin fetch for other banks ---
def fetch_from_minfin(bank_name):
    """Fetch USD and EUR rates for given bank from minfin.com.ua"""
    url = "https://minfin.com.ua/ua/currency/banks/"
    try:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        out = []

        bank_blocks = soup.find_all("div", class_="currency-table__row")
        for block in bank_blocks:
            title_tag = block.find("div", class_="currency-table__title")
            if not title_tag:
                continue
            name = title_tag.get_text(strip=True)
            if bank_name.lower() not in name.lower():
                continue

            cells = block.find_all("div", class_="currency-table__cell")
            # Проверяем, что есть кратное 3
            if len(cells) < 3:
                continue

            for i in range(0, len(cells), 3):
                if i+2 >= len(cells):
                    continue
                currency = cells[i].get_text(strip=True)
                if currency not in ("USD", "EUR"):
                    continue
                try:
                    buy_text = cells[i+1].get_text(strip=True).replace(",", ".")
                    sell_text = cells[i+2].get_text(strip=True).replace(",", ".")
                    buy = float(buy_text)
                    sell = float(sell_text)
                except:
                    continue
                out.append({
                    "bank": bank_name,
                    "currency": currency,
                    "buy": buy,
                    "sell": sell,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        return out
    except Exception as e:
        log_error(f"{bank_name} fetch error (Minfin)", e)
        return []


# --- Banks via minfin ---
def fetch_oschadbank():
    return fetch_from_minfin("Ощадбанк")

def fetch_pumb():
    return fetch_from_minfin("ПУМБ")

def fetch_raiffeisen():
    return fetch_from_minfin("Райффайзен")



# --- 3. SAVE ---
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
