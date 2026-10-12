from app.service import memory


def test_save_and_load(isolated_sqlite):
    memory.save_turn("s1", "u1", "q1", "a1", "conceptual", [])
    memory.save_turn("s1", "u1", "q2", "a2", "live_data", ["AAPL"])
    hist = memory.load_history("s1", limit=5)
    assert len(hist) == 2
    assert hist[0]["query"] == "q1"
    assert hist[1]["query"] == "q2"


def test_load_empty(isolated_sqlite):
    assert memory.load_history("nope") == []