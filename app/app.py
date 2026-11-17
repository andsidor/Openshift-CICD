import re

import requests
from flask import Flask, jsonify

app = Flask(__name__)

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
SYMBOL_RE = re.compile(r"^[A-Za-z0-9.\-^=]{1,15}$")


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
    return jsonify(message="Stock price API", usage="/price/<symbol>, e.g. /price/AAPL")


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
