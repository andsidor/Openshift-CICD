from unittest.mock import patch

import app.app as app_module
from app.app import app


def test_health():
    assert app.test_client().get("/healthz").json == {"status": "ok"}


def test_invalid_symbol():
    assert app.test_client().get("/price/<bad>").status_code in (400, 404)


def test_price():
    fake = {"symbol": "AAPL", "price": 1.0, "currency": "USD", "exchange": "NMS"}
    with patch("app.app.fetch_price", return_value=fake):
        resp = app.test_client().get("/price/aapl")
    assert resp.json == fake


def test_load_symbols(tmp_path, monkeypatch):
    f = tmp_path / "stocks.txt"
    f.write_text("# comment\naapl\nMSFT  # inline\n\nAAPL\n<bad>\n")
    monkeypatch.setattr("app.app.STOCKS_FILE", str(f))
    assert app_module.load_symbols() == ["AAPL", "MSFT"]


def test_prices(tmp_path, monkeypatch):
    f = tmp_path / "stocks.txt"
    f.write_text("AAPL\nXXXX\n")
    monkeypatch.setattr("app.app.STOCKS_FILE", str(f))

    def fake(symbol):
        if symbol == "XXXX":
            raise LookupError(symbol)
        return {"symbol": symbol, "price": 1.0}

    with patch("app.app.fetch_price", side_effect=fake):
        resp = app.test_client().get("/prices")
    assert resp.json["prices"] == [
        {"symbol": "AAPL", "price": 1.0},
        {"symbol": "XXXX", "error": "symbol not found"},
    ]


def test_prices_missing_file(monkeypatch):
    monkeypatch.setattr("app.app.STOCKS_FILE", "/nonexistent")
    assert app.test_client().get("/prices").status_code == 500
