"""测试 /api/context。"""

from backend.services.context_service import get_current_context


def test_context_returns_valid_context(client):
    """验证 context 接口返回字段范围合法。"""

    response = client.get("/api/context")

    assert response.status_code == 200
    payload = response.json()
    assert 0 <= payload["hour"] <= 23
    assert payload["active_app"]
    assert payload["kpm"] >= 0
    assert 0 <= payload["backspace_ratio"] <= 1


def test_context_prefers_activitywatch_when_enabled(monkeypatch):
    monkeypatch.setattr("backend.services.context_service.settings.enable_activitywatch", True)
    monkeypatch.setattr(
        "backend.services.context_service.get_activitywatch_active_app",
        lambda: "ActivityWatchApp",
    )
    monkeypatch.setattr("backend.services.context_service.get_active_app", lambda: "FallbackApp")

    payload = get_current_context(kpm=88, backspace_ratio=0.15)

    assert payload["active_app"] == "ActivityWatchApp"
    assert payload["kpm"] == 88
    assert payload["backspace_ratio"] == 0.15
