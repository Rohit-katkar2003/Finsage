from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# make `app` importable when running pytest from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# force test env BEFORE app.config imports
os.environ.setdefault("LOG_DIR", "./.test_logs")
os.environ.setdefault("MODEL_URL", "http://localhost:9999")
os.environ.setdefault("LLM_MODEL", "test-llm")
os.environ.setdefault("EMBEDDING_MODEL", "test-embed")
os.environ.setdefault("CLASSIFICATION_MODEL", "test-classify")
os.environ.setdefault("GUARDRAIL_LLM_ENABLED", "false")


@pytest.fixture
def base_state() -> dict:
    return {
        "input_query": "",
        "session_id": "test-session",
        "user_id": "u-test",
        "history": [],
        "trace": [],
        "attempts": 0,
        "risk_profile": {"level": "moderate", "goal": "long-term growth"},
    }


@pytest.fixture
def fake_llm(monkeypatch):
    """Patch LLMClient.generate/chat/classify/embed on every module that holds a CLIENT."""
    def _make(generate_return="", chat_return="", classify_return=None):
        if classify_return is None:
            classify_return = {"choices": [{"message": {"content": "{}"}}]}
        mocks = {
            "generate": MagicMock(return_value=generate_return),
            "chat": MagicMock(return_value=chat_return),
            "classify": MagicMock(return_value=classify_return),
            "embed": MagicMock(return_value={"embeddings": [[0.0] * 8]}),
        }

        for mod_name in (
            "app.nodes.intent_route",
            "app.nodes.query_rewriter",
            "app.nodes.generator_node",
            "app.tools.sentiment",
        ):
            mod = __import__(mod_name, fromlist=["CLIENT"])
            client = getattr(mod, "CLIENT", None)
            if client is None:
                continue
            for name, mock in mocks.items():
                monkeypatch.setattr(client, name, mock, raising=False)
        return mocks

    return _make


@pytest.fixture
def fake_yf(monkeypatch):
    """Replace yfinance.Ticker with a stub returning deterministic data."""
    class _FakeTicker:
        def __init__(self, symbol: str):
            self.symbol = symbol

        @property
        def info(self):
            return {
                "longName": f"{self.symbol} Inc.",
                "sector": "Technology",
                "currency": "USD",
                "currentPrice": 100.0,
                "marketCap": 1_000_000_000,
                "trailingPE": 20.0,
                "priceToBook": 4.0,
                "returnOnEquity": 0.25,
                "profitMargins": 0.15,
                "beta": 1.1,
                "fiftyTwoWeekHigh": 150.0,
                "fiftyTwoWeekLow": 80.0,
                "longBusinessSummary": "Fake company for tests.",
            }

        def history(self, period="1y", auto_adjust=True):
            import pandas as pd
            idx = pd.date_range("2024-01-01", periods=250, freq="B")
            return pd.DataFrame({"Close": [100 + i * 0.1 for i in range(250)]}, index=idx)

        @property
        def news(self):
            return [
                {"content": {
                    "title": f"{self.symbol} beats expectations",
                    "summary": "Strong quarter.",
                    "provider": {"displayName": "TestNews"},
                    "canonicalUrl": {"url": "https://example.com/a"},
                    "pubDate": "2024-06-01T00:00:00Z",
                }},
                {"content": {
                    "title": f"{self.symbol} faces headwinds",
                    "summary": "Regulatory concerns.",
                    "provider": {"displayName": "TestWire"},
                    "canonicalUrl": {"url": "https://example.com/b"},
                    "pubDate": "2024-06-02T00:00:00Z",
                }},
            ]

    import yfinance as yf
    monkeypatch.setattr(yf, "Ticker", _FakeTicker)
    return _FakeTicker


@pytest.fixture(autouse=True)
def isolated_sqlite(tmp_path, monkeypatch):
    """Use a temp memory.db per test."""
    db = tmp_path / "memory.db"
    from app.service import memory as mem
    monkeypatch.setattr(mem, "DB", db)
    yield db