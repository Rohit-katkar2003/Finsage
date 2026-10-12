import math

import pytest

from app.tools.calculator import (
    cagr,
    compute_metrics,
    max_drawdown,
    rsi,
    sma,
    volatility,
)


def test_cagr():
    assert cagr(100, 121, 2) == pytest.approx(0.1, abs=1e-6)


def test_cagr_invalid():
    assert cagr(0, 100, 1) is None
    assert cagr(100, 100, 0) is None


def test_volatility_needs_enough_points():
    assert volatility([100, 101]) is None
    v = volatility([100 + i * 0.1 for i in range(50)])
    assert v is not None and v >= 0


def test_max_drawdown():
    assert max_drawdown([100, 80, 90, 70, 120]) == pytest.approx(-0.3, abs=1e-9)


def test_sma():
    assert sma([1, 2, 3, 4, 5], 5) == 3.0
    assert sma([1, 2], 5) is None


def test_rsi_all_up():
    prices = [float(i) for i in range(1, 30)]
    assert rsi(prices, 14) == 100.0


def test_rsi_flat():
    assert rsi([100.0] * 30, 14) == 100.0  # no losses -> 100


def test_compute_metrics_shape():
    market = {
        "AAPL": {
            "ticker": "AAPL",
            "prices": [100 + i * 0.1 for i in range(260)],
            "pe_ratio": 25.0,
            "beta": 1.2,
        }
    }
    m = compute_metrics(market)
    assert "AAPL" in m
    for key in ("1y_return", "volatility_1y", "max_drawdown_1y", "rsi_14"):
        assert key in m["AAPL"]


def test_compute_metrics_error_passthrough():
    m = compute_metrics({"X": {"error": "boom"}})
    assert m["X"]["error"] == "boom"