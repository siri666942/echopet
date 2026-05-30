"""测试 embedding 推荐器。"""


def test_recommend_playlist_orders_by_embedding(client, db_session, monkeypatch):
    monkeypatch.setattr("backend.services.recommender.embed_text", lambda text: [0.0, 1.0, 0.0])

    from backend.models.schemas import ContextModel
    from backend.services.recommender import recommend_playlist

    playlist = recommend_playlist(
        db=db_session,
        retrieval_query="明亮快速",
        context=ContextModel(hour=12, active_app="Test", kpm=0, backspace_ratio=0.0),
        user_profile={},
        top_k=2,
    )

    assert [song.id for song in playlist] == ["s002", "s001"]
