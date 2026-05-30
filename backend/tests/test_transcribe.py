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
