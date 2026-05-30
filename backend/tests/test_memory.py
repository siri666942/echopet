"""测试 /api/memory。"""


def test_memory_pagination(client, monkeypatch):
    """验证 memory 分页参数 limit/offset 生效。"""

    monkeypatch.setattr("backend.services.recommender.embed_text", lambda text: [1.0, 0.0, 0.0])

    # 先通过 analyze 写入两条记忆。
    for text in ["我想专注一下", "今天有点累"]:
        client.post(
            "/api/analyze",
            json={
                "text": text,
                "input_source": "text",
                "context": {
                    "hour": 10,
                    "active_app": "Cursor",
                    "kpm": 60,
                    "backspace_ratio": 0.1,
                },
            },
        )

    # limit=1 表示只取 1 条；offset=1 表示跳过最新的第 1 条。
    response = client.get("/api/memory?limit=1&offset=1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["entries"]) == 1
