from app.tools.market_data import fetch_market_data


def test_fetch_returns_expected_fields(fake_yf):
    data = fetch_market_data(["AAPL"], period="1y")
    d = data["AAPL"]
    assert d["ticker"] == "AAPL"
    assert d["pe_ratio"] == 20.0
    assert isinstance(d["prices"], list) and len(d["prices"]) == 250


def test_fetch_handles_error(monkeypatch):
    import yfinance as yf

    def boom(_):  # noqa: ARG001
        raise RuntimeError("no network")

    monkeypatch.setattr(yf, "Ticker", boom)
    out = fetch_market_data(["AAPL"])
    assert out["AAPL"]["error"]