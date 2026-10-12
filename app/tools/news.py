from __future__ import annotations
import logging, os
from typing import Any
import yfinance as yf
from ..config import get_settings 

log = logging.getLogger(__name__)

def _from_yf(ticker: str, limit: int) -> list[dict]:
    items = []
    try:
        for n in (yf.Ticker(ticker).news or [])[:limit]:
            content = n.get("content") or {}
            title = content.get("title") or n.get("title") or ""
            summary = content.get("summary") or n.get("summary") or ""
            publisher = ((content.get("provider") or {}).get("displayName")
                         or n.get("publisher") or "")
            link = ((content.get("canonicalUrl") or {}).get("url")
                    or n.get("link") or "")
            ts = content.get("pubDate") or n.get("providerPublishTime")
            items.append({
                "ticker": ticker, "title": title, "summary": summary,
                "publisher": publisher, "url": link, "published": ts,
            })
    except Exception as e:
        log.warning("yf news failed for %s: %s", ticker, e)
    return items

def _from_newsapi(query: str, limit: int) -> list[dict]:
    key = os.getenv("NEWSAPI_KEY") 
    log.info(f"newapi key  :  {get_settings().NEWS_API}")
    if not key:
        return []
    try:
        import httpx
        r = httpx.get(
            "https://newsapi.org/v2/everything",
            params={"q": query, "pageSize": limit, "sortBy": "publishedAt",
                    "language": "en", "apiKey": get_settings().NEWS_API},
            timeout=15,
        )
        r.raise_for_status()
        return [
            {"ticker": None, "title": a.get("title", ""),
             "summary": a.get("description", ""),
             "publisher": (a.get("source") or {}).get("name", ""),
             "url": a.get("url", ""), "published": a.get("publishedAt")}
            for a in r.json().get("articles", [])
        ]
    except Exception as e:
        log.warning("newsapi failed: %s", e)
        return []

def fetch_news(tickers: list[str], query: str = "", limit_per: int = 6) -> list[dict]:
    news: list[dict] = []
    for t in tickers:
        news.extend(_from_yf(t, limit_per))
    if not news and query:
        news.extend(_from_newsapi(query, 10))
    # de-dupe by title
    log.info(f"News : {news}")
    seen, out = set(), []
    for n in news:
        k = (n.get("title") or "").strip().lower()
        if k and k not in seen:
            seen.add(k); out.append(n)
    return out[:20]