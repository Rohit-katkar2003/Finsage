from __future__ import annotations
import time
from ..schemas import AgentState


def fallback_node(state: AgentState):
    attempts = state.get("attempts", 0)
    if attempts >= 2:
        # give up — return a graceful message and stop retrying
        return {
            "answer": ("I don't have enough verified data to answer this reliably. "
                       "Please rephrase or provide a specific company/ticker.\n\n"
                       "This is not financial advice."),
            "verification": {"ok": True, "unsupported": [], "notes": "gave_up"},
            "trace": [{"node": "fallback", "action": "give_up",
                       "t": round(time.time(), 3)}],
        }
    return {
        "trace": [{"node": "fallback", "action": "retry",
                   "t": round(time.time(), 3)}],
    }