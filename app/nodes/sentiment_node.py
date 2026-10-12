from __future__ import annotations
import time
from ..schemas import AgentState
from ..tools import score_news

def sentiment_node(state: AgentState):
    news = state.get("news") or []
    if not news:
        return {"sentiment": {"overall": "neutral", "score": 0.0},
                "trace": [{"node": "sentiment", "n": 0}]}
    s = score_news(news)
    return {
        "sentiment": s,
        "trace": [{"node": "sentiment",
                   "overall": s.get("overall"), "score": s.get("score"),
                   "t": round(time.time(), 3)}],
    }