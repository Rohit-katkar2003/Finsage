from __future__ import annotations
import time , logging 
from ..schemas import AgentState
from ..tools import fetch_market_data

logger = logging.getLogger(__name__) 
def market_data_node(state: AgentState):
    tickers = state.get("tickers") or []
    if not tickers:
        return {"market_data": {}, "trace": [{"node": "market_data", "tickers": 0}]}

    logger.info(f"[market_data_node] Tickers : {tickers}") 

    data = fetch_market_data(tickers, period="1y")
    logger.info(f"[market_data_node] Data : {data}")
    return {
        "market_data": data,
        "trace": [{"node": "market_data", "tickers": tickers,
                   "ok": sum(1 for v in data.values() if not v.get("error")),
                   "t": round(time.time(), 3)}],
    }