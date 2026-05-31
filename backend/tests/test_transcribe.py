"""测试 /api/transcribe 的请求校验。"""


def test_transcribe_rejects_missing_audio(client):
    """缺少 audio 字段时，FastAPI/Pydantic 应该返回 422。"""

    response = client.post("/api/transcribe", json={"audio_format": "wav"})

    assert response.status_code == 422


def test_transcribe_rejects_invalid_base64(client):
    """audio 不是合法 Base64 时，后端应该返回 422。"""

    response = client.post(
        "/api/transcribe",
        json={"audio": "not base64!!!", "audio_format": "wav"},
    )

    assert response.status_code == 422


def test_transcribe_returns_503_when_model_unavailable(client, monkeypatch):
    monkeypatch.setattr(
        "backend.services.whisper_service._get_model",
        lambda: None,
    )
    monkeypatch.setattr(
        "backend.services.whisper_service._model_error_message",
        "faster-whisper import or model init failed: missing package",
    )

    response = client.post(
        "/api/transcribe",
        json={"audio": "UklGRg==", "audio_format": "wav"},
    )

    assert response.status_code == 503
    assert "transcribe backend unavailable" in response.json()["detail"]


def test_transcribe_returns_422_when_transcript_is_empty(client, monkeypatch):
    class DummyModel:
        def transcribe(self, _path, language="zh", beam_size=5):
            class Info:
                language = "zh"

            return [], Info()

    monkeypatch.setattr("backend.services.whisper_service._get_model", lambda: DummyModel())

    response = client.post(
        "/api/transcribe",
        json={"audio": "UklGRg==", "audio_format": "wav"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "transcript is empty, no speech detected"
