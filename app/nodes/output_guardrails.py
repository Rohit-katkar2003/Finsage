from __future__ import annotations
import time
from ..schemas import AgentState

DISCLAIMER = "This is not financial advice."

def output_guardrails_node(state: AgentState):
    answer = (state.get("answer") or "").strip()

    if DISCLAIMER not in answer:
        answer = answer.rstrip() + "\n\n" + DISCLAIMER

    # crude confidence from verification + sentiment availability
    v = state.get("verification") or {}
    conf = 0.9 if v.get("ok") and not v.get("unsupported") else 0.6
    if state.get("intent") == "live_data" and not state.get("market_data"):
        conf = 0.3

    # citations from tickers + news publishers
    cites = []
    for t in state.get("tickers") or []:
        cites.append(f"yfinance:{t}")
    for n in (state.get("news") or [])[:5]:
        if n.get("publisher"):
            cites.append(f"news:{n['publisher']}")
    cites = list(dict.fromkeys(cites))

    return {
        "answer": answer,
        "citations": cites,
        "confidence": round(conf, 2),
        "trace": [{"node": "output_guardrails",
                   "confidence": round(conf, 2),
                   "citations": len(cites),
                   "t": round(time.time(), 3)}],
    }