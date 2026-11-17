import os
import re
from concurrent.futures import ThreadPoolExecutor

import requests
from flask import Flask, jsonify

app = Flask(__name__)

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
SYMBOL_RE = re.compile(r"^[A-Za-z0-9.\-^=]{1,15}$")
STOCKS_FILE = os.environ.get("STOCKS_FILE", "k8s/stocks.txt")


def load_symbols() -> list:
    symbols = []
    with open(STOCKS_FILE, encoding="utf-8") as f:
        for line in f:
            symbol = line.split("#", 1)[0].strip().upper()
            if symbol and SYMBOL_RE.match(symbol) and symbol not in symbols:
                symbols.append(symbol)
    return symbols


def fetch_price(symbol: str) -> dict:
    resp = requests.get(
        YAHOO_URL.format(symbol=symbol),
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10,
    )
    resp.raise_for_status()
    result = resp.json()["chart"]["result"]
    if not result:
        raise LookupError(symbol)
    meta = result[0]["meta"]
    return {
        "symbol": meta["symbol"],
        "price": meta["regularMarketPrice"],
        "currency": meta.get("currency"),
        "exchange": meta.get("exchangeName"),
    }


@app.get("/")
def index():
    return jsonify(message="Stock price API", usage="/price/<symbol>, e.g. /price/AAPL; /prices for all symbols from the stocks file")


@app.get("/healthz")
def healthz():
    return jsonify(status="ok")


@app.get("/price/<symbol>")
def price(symbol):
    if not SYMBOL_RE.match(symbol):
        return jsonify(error="invalid symbol"), 400
    try:
        return jsonify(fetch_price(symbol.upper()))
    except (LookupError, KeyError):
        return jsonify(error="symbol not found"), 404
    except requests.RequestException:
        return jsonify(error="upstream API error"), 502


def safe_price(symbol: str) -> dict:
    try:
        return fetch_price(symbol)
    except (LookupError, KeyError):
        return {"symbol": symbol, "error": "symbol not found"}
    except requests.RequestException:
        return {"symbol": symbol, "error": "upstream API error"}


@app.get("/stocks")
def stocks():
    try:
        return jsonify(symbols=load_symbols())
    except OSError:
        return jsonify(error="stocks file not readable"), 500


@app.get("/prices")
def prices():
    try:
        symbols = load_symbols()
    except OSError:
        return jsonify(error="stocks file not readable"), 500
    with ThreadPoolExecutor(max_workers=5) as pool:
        return jsonify(prices=list(pool.map(safe_price, symbols)))
