"""测试 /api/player/status。"""


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
