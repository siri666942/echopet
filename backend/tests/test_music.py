"""测试 /api/music/random。"""


def test_random_music_returns_sample_song(client):
    """验证随机歌曲接口能从样例曲库返回一首歌。"""

    response = client.get("/api/music/random")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"].startswith("s")
    assert payload["title"]
    assert isinstance(payload["tags"], list)
