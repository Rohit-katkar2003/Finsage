from __future__ import annotations
import math
from statistics import mean, pstdev

def _ret(series: list[float]) -> float | None:
    if len(series) < 2 or series[0] == 0:
        return None
    return (series[-1] / series[0]) - 1.0

def cagr(begin: float, end: float, years: float) -> float | None:
    if begin is None or end is None or years <= 0 or begin <= 0:
        return None
    return (end / begin) ** (1.0 / years) - 1.0

def volatility(prices: list[float], periods_per_year: int = 252) -> float | None:
    if len(prices) < 20:
        return None
    rets = [(prices[i] / prices[i-1]) - 1 for i in range(1, len(prices)) if prices[i-1]]
    return pstdev(rets) * math.sqrt(periods_per_year)

def max_drawdown(prices: list[float]) -> float | None:
    if not prices:
        return None
    peak, mdd = prices[0], 0.0
    for p in prices:
        peak = max(peak, p)
        if peak > 0:
            mdd = min(mdd, (p / peak) - 1.0)
    return mdd

def sma(prices: list[float], window: int) -> float | None:
    if len(prices) < window:
        return None
    return mean(prices[-window:])

def rsi(prices: list[float], window: int = 14) -> float | None:
    if len(prices) < window + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(prices)):
        d = prices[i] - prices[i-1]
        gains.append(max(d, 0.0)); losses.append(max(-d, 0.0))
    g, l = mean(gains[-window:]), mean(losses[-window:])
    if l == 0:
        return 100.0
    rs = g / l
    return 100 - (100 / (1 + rs))

def compute_metrics(market: dict) -> dict:
    """Compute per-ticker derived metrics from fetched data."""
    out: dict[str, dict] = {}
    for t, d in market.items():
        if d.get("error"):
            out[t] = {"error": d["error"]}
            continue
        p = d.get("prices") or []
        m = {
            "1y_return": _ret(p),
            "6m_return": _ret(p[-130:]) if len(p) >= 130 else None,
            "1m_return": _ret(p[-22:]) if len(p) >= 22 else None,
            "cagr_1y":  cagr(p[0], p[-1], 1.0) if len(p) >= 2 else None,
            "volatility_1y": volatility(p),
            "max_drawdown_1y": max_drawdown(p),
            "sma_50": sma(p, 50),
            "sma_200": sma(p, 200),
            "rsi_14": rsi(p, 14),
            "pe_ratio": d.get("pe_ratio"),
            "pb_ratio": d.get("pb_ratio"),
            "roe": d.get("roe"),
            "dividend_yield": d.get("dividend_yield"),
            "beta": d.get("beta"),
        }
        out[t] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in m.items()}
    return out