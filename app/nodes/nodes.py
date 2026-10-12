
import time
from ..schemas import AgentState
from ..service import load_history


def _trace(state: AgentState, node: str, **info) -> list[dict]:
    return [{"node": node, "t": round(time.time(), 3), **info}]


def memory_load_node(state: AgentState):
    history = load_history(state.get("session_id", "default"), limit=5)
    return {
        "history": history,
        "trace": _trace(state, "memory_load", n=len(history)),
    }