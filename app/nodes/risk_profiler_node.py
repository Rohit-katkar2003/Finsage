from __future__ import annotations
import time
from ..schemas import AgentState

_VALID = {"conservative", "moderate", "aggressive"}

def risk_profiler_node(state: AgentState):
    rp = dict(state.get("risk_profile") or {})
    level = (rp.get("level") or "moderate").lower()
    if level not in _VALID:
        level = "moderate"
    rp.setdefault("level", level)
    rp.setdefault("goal", "long-term growth")
    rp.setdefault("horizon_years", 5)
    return {
        "risk_profile": rp,
        "trace": [{"node": "risk_profiler", "level": level,
                   "t": round(time.time(), 3)}],
    }