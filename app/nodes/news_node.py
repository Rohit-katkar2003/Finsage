from __future__ import annotations
import time
from ..schemas import AgentState
from ..tools import fetch_news

def news_node(state: AgentState):
    tickers = state.get("tickers") or []
    query = state.get("rewritten_query") or state.get("query") or ""
    news = fetch_news(tickers, query=query, limit_per=6)
    return {
        "news": news,
        "trace": [{"node": "news", "n": len(news), "t": round(time.time(), 3)}],
    }