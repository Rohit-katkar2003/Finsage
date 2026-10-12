from __future__ import annotations
import json, sqlite3, time
from pathlib import Path

DB = Path("memory.db")

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB, check_same_thread=False)
    c.execute("""
        CREATE TABLE IF NOT EXISTS turns (
            session_id TEXT, user_id TEXT, query TEXT, answer TEXT,
            intent TEXT, tickers TEXT, ts REAL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            session_id TEXT, query TEXT, rating INTEGER, ts REAL
        )
    """)
    c.commit()
    return c

def load_history(session_id: str, limit: int = 5) -> list[dict]:
    c = _conn()
    rows = c.execute(
        "SELECT query, answer FROM turns WHERE session_id=? ORDER BY ts DESC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    c.close()
    return [{"query": q, "answer": a} for q, a in reversed(rows)]

def save_turn(session_id: str, user_id: str, query: str, answer: str,
              intent: str, tickers: list[str]) -> None:
    c = _conn()
    c.execute(
        "INSERT INTO turns VALUES (?,?,?,?,?,?,?)",
        (session_id, user_id, query, answer, intent, json.dumps(tickers), time.time()),
    )
    c.commit()
    c.close()