"""测试 /api/player/status。"""

from backend.models.tables import Song


def test_player_status_defaults_to_idle(client):
    """验证刚启动且未播放时，播放器默认是 idle。"""

    response = client.get("/api/player/status")

    assert response.status_code == 200
    assert response.json() == {
        "player": "mpv",
        "status": "idle",
        "track_id": None,
        "title": None,
        "artist": None,
    }


def test_player_event_updates_session_and_song(client, db_session, monkeypatch):
    monkeypatch.setattr("backend.services.recommender.embed_text", lambda text: [1.0, 0.0, 0.0])
    analyze_response = client.post(
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
    session_id = analyze_response.json()["session_id"]

    response = client.post(
        "/api/player/event",
        json={
            "session_id": session_id,
            "event": "ended",
            "completion_rate": 0.1,
            "ended_reason": "skipped",
        },
    )

    assert response.status_code == 200
    song = db_session.query(Song).filter(Song.id == "s001").first()
    assert song.play_count == 1
    assert song.skip_count == 1
    assert song.avg_completion_rate == 0.1
