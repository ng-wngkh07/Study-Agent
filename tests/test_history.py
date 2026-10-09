from fastapi.testclient import TestClient

from app.history import HistoryStore
from app import server


def test_history_store_round_trip(tmp_path):
    store = HistoryStore(tmp_path / "history.db")
    item_id = store.save("  Vì sao? ", "Vì [S1] và [S2].", [{"book_title": "Sách A"}], "local")
    assert store.list()[0]["question"] == "Vì sao?"
    assert store.get(item_id)["citations"] == [{"book_title": "Sách A"}]
    assert store.delete(item_id)
    assert store.get(item_id) is None


def test_stream_saves_only_completed_answer(tmp_path, monkeypatch):
    store = HistoryStore(tmp_path / "history.db")
    monkeypatch.setattr(server, "history_store", store)

    def completed(**kwargs):
        yield {"type": "token", "content": "Kết luận [S1]."}
        yield {"type": "citations", "citations": [{"book_title": "Sách A"}]}
        yield {"type": "done", "citations": [{"book_title": "Sách A"}]}

    monkeypatch.setattr(server.agent, "process_query_stream", completed)
    with TestClient(server.app) as client:
        response = client.post("/api/chat/stream", json={"query": "Vì sao?"})
        assert response.status_code == 200
        assert "history_id" in response.text
        items = client.get("/api/history").json()["items"]
        assert len(items) == 1
        detail = client.get(f"/api/history/{items[0]['id']}").json()
        assert detail["answer"] == "Kết luận."
        assert len(detail["citations"]) == 1
        assert client.delete(f"/api/history/{items[0]['id']}").status_code == 200

    def interrupted(**kwargs):
        yield {"type": "token", "content": "Dở dang"}
        yield {"type": "error", "content": "mất kết nối"}

    monkeypatch.setattr(server.agent, "process_query_stream", interrupted)
    with TestClient(server.app) as client:
        client.post("/api/chat/stream", json={"query": "Câu hỏi khác"})
        assert client.get("/api/history").json()["items"] == []
