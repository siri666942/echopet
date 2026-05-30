"""测试 /api/analyze 核心链路。"""


def test_analyze_returns_recommendation_and_writes_memory(client):
    """验证 analyze 能完成“文本 -> 情绪 -> 推荐 -> 记忆”。

    这个测试故意不依赖 OpenAI 和 mpv。
    它证明兜底逻辑能跑通：
        - 关键词 debug/烦 会识别成 frustrated
        - 会返回推荐歌曲
        - 会写入 memory 表
    """

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
    assert payload["emotion"]["emotion"] == "frustrated"
    assert payload["current_state"] == "frustrated"
    assert payload["recommendation"]["id"]
    assert payload["play_action"] == "play"
    assert payload["player_status"] in {"idle", "loading", "playing", "error"}

    # 再查 memory，确认 analyze 不只是返回了结果，也真的保存了历史记录。
    memory_response = client.get("/api/memory")
    assert memory_response.status_code == 200
    assert memory_response.json()["total"] == 1
