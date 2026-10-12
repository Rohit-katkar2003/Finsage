from app.tools.news import fetch_news


def test_fetch_yf_news(fake_yf):
    news = fetch_news(["AAPL"], limit_per=5)
    assert len(news) == 2
    assert all("title" in n for n in news)


def test_dedupes(monkeypatch, fake_yf):
    # both tickers return same titles in our fake — dedupe should collapse
    news = fetch_news(["AAPL", "AAPL"], limit_per=5)
    titles = [n["title"] for n in news]
    assert len(titles) == len(set(titles))


def test_newsapi_skipped_without_key(monkeypatch, fake_yf):
    monkeypatch.delenv("NEWSAPI_KEY", raising=False)
    # still fine — no crash
    fetch_news(["AAPL"])