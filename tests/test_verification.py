from app.nodes.verification_node import verification_node


def test_all_numbers_supported(base_state):
    base_state["answer"] = "The P/E is 20.0 [yfinance:AAPL]."
    base_state["metrics"] = {"AAPL": {"pe_ratio": 20.0}}
    base_state["intent"] = "live_data"
    out = verification_node(base_state)
    assert out["verification"]["ok"] is True


def test_unsupported_number_detected(base_state):
    base_state["answer"] = "The P/E is 99.9 [yfinance:AAPL]."
    base_state["metrics"] = {"AAPL": {"pe_ratio": 20.0}}
    base_state["intent"] = "live_data"
    out = verification_node(base_state)
    assert out["verification"]["ok"] is False
    assert "99.9" in out["verification"]["unsupported"]


def test_missing_citation_fails_factual(base_state):
    base_state["answer"] = "The P/E is 20.0."
    base_state["metrics"] = {"AAPL": {"pe_ratio": 20.0}}
    base_state["intent"] = "live_data"
    out = verification_node(base_state)
    assert out["verification"]["ok"] is False


def test_conceptual_no_citation_ok(base_state):
    base_state["answer"] = "The P/E ratio compares price to earnings."
    base_state["intent"] = "conceptual"
    assert verification_node(base_state)["verification"]["ok"] is True