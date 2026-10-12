from __future__ import annotations
import re, time
from ..schemas import AgentState

NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")

def _collect_ground_numbers(state: AgentState) -> set[str]:
    """All numeric strings that appear anywhere in tool outputs."""
    pool: set[str] = set()
    for blob in (
        state.get("market_data") or {},
        state.get("metrics") or {},
        state.get("sentiment") or {},
        state.get("news") or [],
    ):
        for m in NUM_RE.findall(str(blob)):
            pool.add(m)
            # add rounded forms
            try:
                f = float(m)
                pool.add(f"{f:.0f}"); pool.add(f"{f:.1f}"); pool.add(f"{f:.2f}")
            except Exception:
                pass
    return pool


def verification_node(state: AgentState):
    answer = state.get("answer", "") or ""
    ground = _collect_ground_numbers(state)

    # Numbers in the answer that are not grounded
    unsupported = []
    for m in NUM_RE.findall(answer):
        # ignore tiny integers used as ordinals / list items / years
        try:
            f = float(m)
        except Exception:
            continue
        if f.is_integer() and abs(f) < 10:
            continue
        if m not in ground:
            unsupported.append(m)

    # crude hallucination heuristic: no citations at all and factual intent
    has_citation = "[" in answer and "]" in answer
    factual_intent = state.get("intent") in ("live_data", "multi_step", "document")
    ok = len(unsupported) == 0 and (has_citation or not factual_intent)

    notes = ""
    if unsupported:
        notes = f"Unsupported numbers: {unsupported[:8]}"
    elif factual_intent and not has_citation:
        notes = "No citations provided for a factual answer."

    return {
        "verification": {"ok": ok, "unsupported": unsupported, "notes": notes},
        "trace": [{"node": "verify", "ok": ok,
                   "unsupported": len(unsupported),
                   "t": round(time.time(), 3)}],
    }