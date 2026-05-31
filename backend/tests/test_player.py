"""测试 /api/player/status。"""

from backend.models.tables import Song
from backend.services import player_service, playlist_service


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


def test_player_skip_moves_to_next_playlist_song(client, monkeypatch):
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
    assert analyze_response.status_code == 200

    response = client.post("/api/player/skip")

    assert response.status_code == 200
    assert response.json()["track_id"] == "s002"


def test_player_skip_without_next_song_returns_404(client):
    response = client.post("/api/player/skip")

    assert response.status_code == 404


def test_player_stop_clears_status(client, monkeypatch):
    monkeypatch.setattr("backend.services.recommender.embed_text", lambda text: [1.0, 0.0, 0.0])

    analyze_response = client.post(
        "/api/analyze",
        json={
            "text": "我想听点轻松的歌",
            "input_source": "text",
            "context": {
                "hour": 21,
                "active_app": "VSCode",
                "kpm": 80,
                "backspace_ratio": 0.05,
            },
        },
    )
    assert analyze_response.status_code == 200

    response = client.post("/api/player/stop")

    assert response.status_code == 200
    assert response.json() == {
        "player": "mpv",
        "status": "idle",
        "track_id": None,
        "title": None,
        "artist": None,
    }


def test_player_service_toggle_pause_and_resume(monkeypatch):
    class FakePlayer:
        def __init__(self):
            self.pause = False
            self.idle_active = False

        def play(self, _path):
            return None

        def stop(self):
            return None

    fake_player = FakePlayer()
    monkeypatch.setattr("backend.services.player_service.settings.enable_mpv", True)
    monkeypatch.setattr("backend.services.player_service._get_player", lambda: fake_player)

    player_service.play("C:/music/s001.mp3", "s001", "Steady Low", "Test")
    assert player_service.get_status()["status"] == "playing"

    assert player_service.toggle_pause() == "paused"
    assert fake_player.pause is True

    assert player_service.toggle_pause() == "playing"
    assert fake_player.pause is False


def test_player_service_auto_advances_when_current_song_finishes(db_session, monkeypatch):
    class FakePlayer:
        def __init__(self):
            self.pause = False
            self.idle_active = False

        def play(self, _path):
            self.idle_active = False

        def stop(self):
            self.idle_active = True

    songs = db_session.query(Song).order_by(Song.id).all()
    playlist_service.set_playlist(songs)

    fake_player = FakePlayer()
    monkeypatch.setattr("backend.services.player_service.settings.enable_mpv", True)
    monkeypatch.setattr("backend.services.player_service._get_player", lambda: fake_player)
    now = {"value": 100.0}
    monkeypatch.setattr(
        "backend.services.player_service.time.monotonic",
        lambda: now["value"],
    )

    player_service.play(songs[0].file_path, songs[0].id, songs[0].title, songs[0].artist)
    fake_player.idle_active = True
    now["value"] = 103.0

    status = player_service.get_status()

    assert status["track_id"] == "s002"
    assert status["status"] in {"loading", "playing"}


def test_player_service_loading_grace_prevents_consuming_playlist(db_session, monkeypatch):
    class FakePlayer:
        def __init__(self):
            self.pause = False
            self.idle_active = True

        def play(self, _path):
            return None

        def stop(self):
            self.idle_active = True

    songs = db_session.query(Song).order_by(Song.id).all()
    playlist_service.set_playlist(songs)

    fake_player = FakePlayer()
    monkeypatch.setattr("backend.services.player_service.settings.enable_mpv", True)
    monkeypatch.setattr("backend.services.player_service._get_player", lambda: fake_player)
    monkeypatch.setattr("backend.services.player_service._loading_grace_seconds", 2.0)
    monkeypatch.setattr("backend.services.player_service.time.monotonic", lambda: 100.0)

    player_service.play(songs[0].file_path, songs[0].id, songs[0].title, songs[0].artist)

    status = player_service.get_status()

    assert status["track_id"] == songs[0].id
    assert status["status"] == "loading"
