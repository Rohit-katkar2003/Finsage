from __future__ import annotations
import time
from ..schemas import AgentState
from ..tools import compute_metrics

def calculator_node(state: AgentState):
    market = state.get("market_data") or {}
    metrics = compute_metrics(market) if market else {}
    return {
        "metrics": metrics,
        "trace": [{"node": "calculator", "tickers": list(metrics.keys()),
                   "t": round(time.time(), 3)}],
    }