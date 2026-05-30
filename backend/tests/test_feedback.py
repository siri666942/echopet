"""测试 /api/feedback。"""


def test_feedback_success(client):
    """已存在歌曲 + 合法反馈，应该返回 ok。"""

    response = client.post(
        "/api/feedback",
        json={"song_id": "s001", "feedback": "positive"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_feedback_unknown_song(client):
    """不存在的 song_id 应该返回 404。"""

    response = client.post(
        "/api/feedback",
        json={"song_id": "missing", "feedback": "positive"},
    )

    assert response.status_code == 404


def test_feedback_rejects_invalid_feedback(client):
    """非法 feedback 值应该被 Pydantic 拦截，返回 422。"""

    response = client.post(
        "/api/feedback",
        json={"song_id": "s001", "feedback": "bad"},
    )

    assert response.status_code == 422
