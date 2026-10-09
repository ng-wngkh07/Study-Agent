import json
import sqlite3
from contextlib import nullcontext
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import server, topic_summarizer
from app.history import HistoryStore
from app.topic_summarizer import TopicSummarizer


@pytest.mark.parametrize('payload', [
    {'title': None, 'summary': 'Nội dung hợp lệ.'},
    {'title': 'Chủ đề', 'summary': ['không phải văn bản']},
    {'title': 'Chủ đề', 'summary': {'text': 'không phải văn bản'}},
])
def test_summary_requires_string_fields(tmp_path, payload):
    summarizer = TopicSummarizer(HistoryStore(tmp_path / 'history.db'))
    assert summarizer._parse_summary_response(json.dumps(payload)) is None


def test_truncated_generation_never_completes_summary(tmp_path, monkeypatch):
    store = HistoryStore(tmp_path / 'history.db')
    sid = store.create_session()['id']
    store.add_turn(sid, 'Thói quen được hình thành thế nào?', 'Qua các lượt thực hành.', [], 'mock')
    ollama = SimpleNamespace(
        check_health=lambda: True,
        last_done_reason='length',
        chat_complete=lambda **kwargs: json.dumps({'title': 'Hình thành thói quen', 'summary': 'Trao đổi về việc thực hành.'}),
    )
    monkeypatch.setattr(topic_summarizer, 'gpu_coordinator', SimpleNamespace(
        check_inference_allowed=lambda: (True, ''),
        acquire_for_inference=nullcontext,
    ))
    result = TopicSummarizer(store, ollama).summarize_session_sync(sid)
    assert result['status'] != 'completed'
    assert store.get_session(sid)['summary'] is None


@pytest.fixture
def isolated_api(tmp_path, monkeypatch):
    store = HistoryStore(tmp_path / 'history.db')
    monkeypatch.setattr(server, 'history_store', store)
    monkeypatch.setattr(server, 'gpu_coordinator', SimpleNamespace(
        check_inference_allowed=lambda: (True, ''),
        acquire_for_inference=nullcontext,
    ))
    return TestClient(server.app), store


@pytest.mark.parametrize('route', ['/api/chat', '/api/chat/stream'])
def test_replay_cannot_switch_to_a_different_session(isolated_api, route):
    client, store = isolated_api
    first = store.create_session()['id']
    second = store.create_session()['id']
    store.add_turn(first, 'Câu hỏi chung', 'Đáp trong phiên đầu.', [], 'mock', request_id='request-a')
    response = client.post(route, json={
        'query': 'Câu hỏi chung', 'session_id': second, 'request_id': 'request-a', 'model': 'mock',
    })
    assert response.status_code == 409
    assert store.get_session(second)['turns'] == []


def test_sync_error_does_not_save_a_completed_turn(isolated_api, monkeypatch):
    client, store = isolated_api
    monkeypatch.setattr(server.agent, 'process_query_sync', lambda **kwargs: {
        'answer': 'Câu trả lời dở dang', 'error': 'mất kết nối',
    })
    response = client.post('/api/chat', json={'query': 'Một câu hỏi'})
    assert response.status_code == 200
    assert store.list_sessions()['total'] == 0
    assert store.list() == []


def test_migration_backup_keeps_the_original_schema(tmp_path):
    path = tmp_path / 'old.db'
    with sqlite3.connect(path) as db:
        db.execute('''CREATE TABLE searches (
            id INTEGER PRIMARY KEY, created_at TEXT, question TEXT,
            answer TEXT, citations_json TEXT, model TEXT)''')
        db.execute("INSERT INTO searches VALUES(20, '2026-10-01', 'Câu cũ', 'Đáp cũ', '[]', 'mock')")
    store = HistoryStore(path, auto_init=False)
    report = store.migrate_legacy_searches()
    with sqlite3.connect(report['backup_path']) as backup:
        tables = {r[0] for r in backup.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert 'sessions' not in tables
        assert backup.execute('SELECT question FROM searches WHERE id=20').fetchone()[0] == 'Câu cũ'
    assert store.get_session('legacy_20')['turns'][0]['question'] == 'Câu cũ'
