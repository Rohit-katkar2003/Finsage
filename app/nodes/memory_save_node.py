from __future__ import annotations
import time
from ..schemas import AgentState
from ..service import save_turn


def memory_save_node(state: AgentState):
    try:
        save_turn(
            session_id=state.get("session_id", "default"),
            user_id=state.get("user_id", "anon"),
            query=state.get("query", ""),
            answer=state.get("answer", ""),
            intent=state.get("intent", ""),
            tickers=state.get("tickers", []) or [],
        )
        ok = True
    except Exception:
        ok = False

    return {"trace": [{"node": "memory_save", "ok": ok,
                       "t": round(time.time(), 3)}]}