from app.tools.sentiment import score_news


def test_empty_news():
    assert score_news([])["overall"] == "neutral"


def test_parses_llm_json(fake_llm):
    fake_llm(generate_return='{"overall":"positive","score":0.6,'
                             '"rationale":"strong Q","items":[]}')
    news = [{"title": "AAPL beats", "summary": ""}]
    out = score_news(news)
    assert out["overall"] == "positive"
    assert out["score"] == 0.6


def test_bad_json_falls_back(fake_llm):
    fake_llm(generate_return="not json at all")
    news = [{"title": "x", "summary": ""}]
    out = score_news(news)
    assert out["overall"] == "neutral"