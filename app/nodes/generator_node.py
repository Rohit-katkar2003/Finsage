from __future__ import annotations
import json, logging, time
from ..schemas import AgentState
from ..client import LLMClient

log = logging.getLogger(__name__)
CLIENT = LLMClient()

SYSTEM = """You are a financial research assistant.

STRICT RULES:
1. Use ONLY the market_data, metrics, news, sentiment, and risk_profile provided.
   Do NOT invent numbers. If data is missing, say so explicitly.
2. NEVER perform arithmetic. Every number you cite must appear verbatim
   in the provided METRICS or MARKET_DATA JSON.
3. Cite sources in square brackets, e.g. [yfinance:AAPL], [news:Reuters].
4. Tailor tone and framing to the user's risk profile.
5. End with this exact line:
   "This is not financial advice."
6. Be concise: 150–300 words. Use short paragraphs or bullets.

You will be given a JSON blob. Treat it as ground truth."""


def _build_context(state: AgentState) -> str:
    payload = {
        "question": state.get("rewritten_query") or state.get("query"),
        "intent": state.get("intent"),
        "tickers": state.get("tickers"),
        "risk_profile": state.get("risk_profile"),
        "market_data": {
            t: {k: v for k, v in d.items() if k != "prices"}
            for t, d in (state.get("market_data") or {}).items()
        },
        "metrics": state.get("metrics") or {},
        "sentiment": state.get("sentiment") or {},
        "news": [
            {"title": n.get("title"), "publisher": n.get("publisher"),
             "sentiment": n.get("sentiment", {}).get("label"),
             "summary": (n.get("summary") or "")[:180]}
            for n in (state.get("news") or [])[:10]
        ],
    }
    return json.dumps(payload, default=str)


def generator_node(state: AgentState):
    feedback = state.get("verification", {}).get("notes") if state.get("attempts", 0) else None
    user_block = _build_context(state)
    if feedback:
        user_block += f"\n\nPREVIOUS ATTEMPT FAILED: {feedback}\nRemove unsupported numbers and try again."

    try:
        answer = CLIENT.generate(
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_block},
            ],
            temperature=0.2, max_tokens=500,
        )
    except Exception as e:
        log.exception("generator failed: %s", e)
        answer = "I don't have enough data to answer this reliably right now."

    return {
        "answer": answer.strip(),
        "attempts": state.get("attempts", 0) + 1,
        "trace": [{"node": "generate", "chars": len(answer),
                   "attempt": state.get("attempts", 0) + 1,
                   "t": round(time.time(), 3)}],
    }