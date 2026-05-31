"""测试 /api/transcribe 的请求校验和失败语义。"""

import base64

from backend.services import whisper_service


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


def test_transcribe_reports_model_unavailable(client, monkeypatch):
    """模型不可用时不能返回 200 + 空 transcript。"""

    whisper_service.reset_model_cache_for_tests()
    monkeypatch.setattr(whisper_service, "_get_model", lambda: None)
    monkeypatch.setattr(whisper_service, "_model_error", "test model load failed")

    audio = base64.b64encode(b"not a real wav but enough to reach model load").decode("ascii")
    response = client.post(
        "/api/transcribe",
        json={"audio": audio, "audio_format": "wav"},
    )

    assert response.status_code == 503
    assert "faster-whisper model unavailable" in response.json()["detail"]
