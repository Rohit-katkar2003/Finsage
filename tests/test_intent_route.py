from app.nodes import intent_route


class TestIntentClassification:
    def test_valid_json(self, base_state, fake_llm):
        fake_llm(generate_return='{"intent": "live_data", "tickers": ["aapl"]}')
        base_state["query"] = "How is Apple doing?"
        out = intent_route.intent_classification(base_state)
        assert out["intent"] == "live_data"
        assert out["tickers"] == ["AAPL"]

    def test_code_fenced_json(self, base_state, fake_llm):
        fake_llm(generate_return='```json\n{"intent":"conceptual","tickers":[]}\n```')
        base_state["query"] = "What is a P/E ratio?"
        out = intent_route.intent_classification(base_state)
        assert out["intent"] == "conceptual"
        assert out["tickers"] == []

    def test_invalid_intent_defaults(self, base_state, fake_llm):
        fake_llm(generate_return='{"intent":"nonsense","tickers":[]}')
        base_state["query"] = "x"
        assert intent_route.intent_classification(base_state)["intent"] == "multi_step"

    def test_llm_error_falls_back(self, base_state, fake_llm):
        mocks = fake_llm()
        mocks["generate"].side_effect = RuntimeError("boom")
        base_state["query"] = "x"
        out = intent_route.intent_classification(base_state)
        assert out["intent"] == "multi_step"
        assert out["tickers"] == []

    def test_caps_tickers_at_three(self, base_state, fake_llm):
        fake_llm(generate_return='{"intent":"multi_step","tickers":["A","B","C","D","E"]}')
        base_state["query"] = "x"
        assert intent_route.intent_classification(base_state)["tickers"] == ["A", "B", "C"]