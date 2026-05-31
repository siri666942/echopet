"""测试用户画像服务。"""

import json

from backend.models.tables import PlaySession
from backend.services.profile_service import (
    _session_to_reflection_payload,
    ensure_user_profile,
    maybe_reflect_profile,
)


def test_ensure_user_profile_creates_default(db_session):
    profile = ensure_user_profile(db_session)
    assert "global_likes" in profile
    assert "implicit_patterns" in profile
    assert "keyboard_baseline" in profile


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


def test_reflection_payload_includes_keyboard_context():
    session = PlaySession(
        id="keyboard-session",
        song_id="s001",
        retrieval_query="稳定音乐",
        playlist_json="[]",
        completion_rate=0.8,
        ended_reason="finished",
        keyboard_state_json=json.dumps(
            {
                "focus": 0.82,
                "stress": 0.71,
                "fatigue": 0.24,
                "stability": 0.66,
                "typing_state": "high_activity_unstable",
            }
        ),
        keyboard_features_json=json.dumps({"kpm": 180, "backspace_ratio": 0.13}),
    )

    payload = _session_to_reflection_payload(session)

    assert payload["keyboard_state"]["typing_state"] == "high_activity_unstable"
    assert payload["keyboard_features"]["kpm"] == 180
    assert payload["completion_rate"] == 0.8
