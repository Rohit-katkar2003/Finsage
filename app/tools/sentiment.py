from __future__ import annotations
import json, logging, re
from ..client import LLMClient

log = logging.getLogger(__name__)
CLIENT = LLMClient()

PROMPT = """You are a financial news sentiment classifier.
Return ONLY JSON:
{"items":[{"i":<index>,"label":"positive|neutral|negative","score":<-1..1>}],
 "overall":"positive|neutral|negative","score":<-1..1>,"rationale":"..."}
Score reflects impact on the stock price. Be strict."""

def score_news(news: list[dict]) -> dict:
    if not news:
        return {"overall": "neutral", "score": 0.0, "items": [], "rationale": "no news"}

    # cap to keep prompt small
    trimmed = [
        {"i": i, "t": n.get("title", ""), "s": (n.get("summary") or "")[:200]}
        for i, n in enumerate(news[:15])
    ]

    try:
        raw = CLIENT.generate(
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": json.dumps(trimmed)},
            ],
            temperature=0, max_tokens=800,
        )
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
        labels = {it.get("i"): it for it in data.get("items", [])}
        for i, n in enumerate(trimmed):
            lbl = labels.get(i, {"label": "neutral", "score": 0.0})
            news[i]["sentiment"] = lbl 

        log.info(f"Sentiment Data : {data}")
        return {
            "overall": data.get("overall", "neutral"),
            "score": float(data.get("score", 0.0)),
            "rationale": data.get("rationale", ""),
            "items": list(labels.values()),
        }
    except Exception as e:
        log.warning("sentiment failed: %s", e)
        return {"overall": "neutral", "score": 0.0, "items": [], "rationale": "unavailable"}