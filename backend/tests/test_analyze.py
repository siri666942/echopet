"""测试 /api/analyze 2.0 主链路。"""

import json

from backend.models.tables import PlaySession


def test_analyze_returns_playlist_and_creates_session(client, monkeypatch):
    monkeypatch.setattr("backend.services.recommender.embed_text", lambda text: [1.0, 0.0, 0.0])

    response = client.post(
        "/api/analyze",
        json={
            "text": "我 debug 一天了，有点烦",
            "input_source": "text",
            "context": {
                "hour": 23,
                "active_app": "VSCode",
                "kpm": 120,
                "backspace_ratio": 0.2,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"]
    assert payload["retrieval_query"]
    assert len(payload["playlist"]) >= 1
    assert payload["recommendation"]["id"] == "s001"
    assert payload["emotion"]["emotion"] == "frustrated"
    assert payload["current_state"] == "frustrated"

    memory_response = client.get("/api/memory")
    assert memory_response.status_code == 200
    assert memory_response.json()["total"] == 1


def test_analyze_accepts_keyboard_events_and_persists_state(client, db_session, monkeypatch):
    monkeypatch.setattr("backend.services.recommender.embed_text", lambda text: [1.0, 0.0, 0.0])

    response = client.post(
        "/api/analyze",
        json={
            "text": "来点适合现在的",
            "input_source": "text",
            "context": {
                "hour": 14,
                "active_app": "VSCode",
                "kpm": 0,
                "backspace_ratio": 0.0,
            },
            "keyboard_events": _high_activity_unstable_events(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["current_state"] == "focused_stressed"
    assert "高强度" in payload["bubble_text"]

    session = db_session.query(PlaySession).filter(PlaySession.id == payload["session_id"]).first()
    keyboard_features = json.loads(session.keyboard_features_json)
    keyboard_state = json.loads(session.keyboard_state_json)
    context = json.loads(session.context_json)

    assert keyboard_features["kpm"] == 180
    assert keyboard_state["typing_state"] == "high_activity_unstable"
    assert "emotion" not in keyboard_state
    assert context["kpm"] == 180


def _high_activity_unstable_events():
    events = []
    timestamp = 0.0
    for index in range(180):
        key = "Backspace" if index % 5 == 0 else "CHAR"
        events.append({"key": key, "type": "keydown", "timestamp": timestamp})
        events.append({"key": key, "type": "keyup", "timestamp": timestamp + 0.04})
        timestamp += 0.05 if index % 2 == 0 else 0.5
    return {"window_seconds": 60, "events": events, "active_app": "VSCode"}
