from unittest.mock import patch

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
