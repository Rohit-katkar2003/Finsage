from __future__ import annotations
import logging
from typing import Any
import yfinance as yf

log = logging.getLogger(__name__)

def _num(v) -> float | None:
    try:
        if v is None:
            return None
        f = float(v)
        return None if f != f else f          # drop NaN
    except Exception:
        return None

def fetch_market_data(tickers: list[str], period: str = "1y") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            info = tk.info or {} 
            log.info(f"Complete Data for Ticker : {t} : Data : {info}")
            hist = tk.history(period=period, auto_adjust=True)
            closes = hist["Close"].dropna().tolist() if not hist.empty else []

            out[t] = {
                "ticker": t,
                "name": info.get("longName") or info.get("shortName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "currency": info.get("currency"),
                "current_price": _num(info.get("currentPrice"))
                                 or _num(info.get("regularMarketPrice")),
                "market_cap": _num(info.get("marketCap")),
                "pe_ratio": _num(info.get("trailingPE")),
                "forward_pe": _num(info.get("forwardPE")),
                "pb_ratio": _num(info.get("priceToBook")),
                "roe": _num(info.get("returnOnEquity")),
                "profit_margin": _num(info.get("profitMargins")),
                "debt_to_equity": _num(info.get("debtToEquity")),
                "dividend_yield": _num(info.get("dividendYield")),
                "beta": _num(info.get("beta")),
                "52w_high": _num(info.get("fiftyTwoWeekHigh")),
                "52w_low": _num(info.get("fiftyTwoWeekLow")),
                "revenue_growth": _num(info.get("revenueGrowth")),
                "earnings_growth": _num(info.get("earningsGrowth")),
                "summary": (info.get("longBusinessSummary") or "")[:600],
                "prices": closes[-260:],
                "error": None,
            }
        except Exception as e:
            log.warning("market data failed for %s: %s", t, e)
            out[t] = {"ticker": t, "error": str(e)}
    return out