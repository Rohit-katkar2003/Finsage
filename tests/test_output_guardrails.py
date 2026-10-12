from app.nodes.output_guardrails import DISCLAIMER, output_guardrails_node


def test_adds_disclaimer(base_state):
    base_state["answer"] = "Something."
    out = output_guardrails_node(base_state)
    assert DISCLAIMER in out["answer"]


def test_does_not_duplicate_disclaimer(base_state):
    base_state["answer"] = f"Something.\n\n{DISCLAIMER}"
    out = output_guardrails_node(base_state)
    assert out["answer"].count(DISCLAIMER) == 1


def test_citations_and_confidence(base_state):
    base_state["answer"] = "See [yfinance:AAPL]."
    base_state["tickers"] = ["AAPL"]
    base_state["news"] = [{"publisher": "Reuters"}]
    base_state["verification"] = {"ok": True, "unsupported": []}
    base_state["intent"] = "live_data"
    out = output_guardrails_node(base_state)
    assert "yfinance:AAPL" in out["citations"]
    assert "news:Reuters" in out["citations"]
    assert out["confidence"] >= 0.9


def test_low_confidence_when_no_market_data(base_state):
    base_state["answer"] = "x"
    base_state["intent"] = "live_data"
    base_state["verification"] = {"ok": True}
    out = output_guardrails_node(base_state)
    assert out["confidence"] <= 0.4