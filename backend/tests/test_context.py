"""测试 /api/context。"""


def test_context_returns_valid_context(client):
    """验证 context 接口返回字段范围合法。"""

    response = client.get("/api/context")

    assert response.status_code == 200
    payload = response.json()
    assert 0 <= payload["hour"] <= 23
    assert payload["active_app"]
    assert payload["kpm"] >= 0
    assert 0 <= payload["backspace_ratio"] <= 1
