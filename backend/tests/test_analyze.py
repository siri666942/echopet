"""测试 /api/analyze 2.0 主链路。"""


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
