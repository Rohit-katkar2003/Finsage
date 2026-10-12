from app.nodes import query_rewriter


def test_rewrites(base_state, fake_llm):
    fake_llm(generate_return="Apple AAPL investment outlook and valuation")
    base_state["query"] = "is it good?"
    base_state["intent"] = "live_data"
    base_state["tickers"] = ["AAPL"]
    out = query_rewriter.query_rewrite(base_state)
    assert "Apple" in out["rewritten_query"]


def test_too_short_uses_original(base_state, fake_llm):
    fake_llm(generate_return="")
    base_state["query"] = "original question"
    out = query_rewriter.query_rewrite(base_state)
    assert out["rewritten_query"] == "original question"


def test_error_uses_original(base_state, fake_llm):
    mocks = fake_llm()
    mocks["generate"].side_effect = RuntimeError("nope")
    base_state["query"] = "original question"
    out = query_rewriter.query_rewrite(base_state)
    assert out["rewritten_query"] == "original question"


def test_history_formatter():
    hist = [{"query": "apple?", "answer": "Apple is..."}]
    s = query_rewriter._format_history(hist)
    assert "user: apple?" in s and "assistant: Apple is" in s


def test_history_empty():
    assert query_rewriter._format_history([]) == "(none)"