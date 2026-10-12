import json, logging

from ..schemas import AgentState
from ..client import LLMClient
log = logging.getLogger(__name__)

CLIENT = LLMClient()
ROUTER_PROMPT = """You classify finance questions.
Reply ONLY with JSON: {"intent": "conceptual|live_data|document|multi_step", "tickers": ["AAPL"]}

- conceptual: definitions/education, no company data needed
- live_data: needs current price, fundamentals or news
- document: needs company filings / reports / PDFs
- multi_step: needs several of the above, or calculations

Tickers must be Yahoo Finance symbols (e.g. RELIANCE.NS, AAPL).
Only return a ticker when a company is explicitly named or clearly implied by the
conversation. For general finance concepts with no company context, return [].
Never use example tickers such as AAPL unless the question is about Apple."""


def intent_classification(state: AgentState):
    try:
        raw = CLIENT.generate(
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": state["query"]},
            ],
            temperature=0,
            max_tokens=100,
        )
        # strip code fences if the model wraps JSON
        print(f"===========>>>>> {raw}")
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)

        intent = data.get("intent", "multi_step")
        if intent not in ("conceptual", "live_data", "document", "multi_step"):
            intent = "multi_step"

        tickers = [t.upper() for t in data.get("tickers", [])][:3]

    except Exception as e:
        log.warning("router failed, defaulting to multi_step: %s", e)
        intent, tickers = "multi_step", []

    return {
        "intent": intent,
        "tickers": tickers,
        "trace": [{"node": "intent", "intent": intent, "tickers": tickers}],
    }
