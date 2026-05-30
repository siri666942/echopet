"""测试用户画像服务。"""

from backend.models.tables import PlaySession
from backend.services.profile_service import ensure_user_profile, maybe_reflect_profile


def test_ensure_user_profile_creates_default(db_session):
    profile = ensure_user_profile(db_session)
    assert "global_likes" in profile
    assert "implicit_patterns" in profile


def test_maybe_reflect_profile_runs_on_ten_sessions(db_session, monkeypatch):
    ensure_user_profile(db_session)
    for i in range(10):
        db_session.add(
            PlaySession(
                id=f"p{i}",
                song_id="s001",
                retrieval_query="稳定音乐",
                playlist_json="[]",
                completion_rate=0.8,
                ended_reason="finished",
            )
        )
    db_session.commit()

    monkeypatch.setattr("backend.services.profile_service.settings.openai_api_key", "test")
    monkeypatch.setattr(
        "backend.services.profile_service._reflect_with_llm",
        lambda profile, sessions: {"global_likes": ["节奏稳定"]},
    )

    maybe_reflect_profile(db_session)
    profile = ensure_user_profile(db_session)
    assert "节奏稳定" in profile["global_likes"]
