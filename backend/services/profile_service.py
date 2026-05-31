"""长期用户画像服务。"""

import json
from datetime import datetime

from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.tables import PlaySession, UserProfile


DEFAULT_PROFILE = {
    "global_likes": [],
    "global_dislikes": [],
    "scene_preferences": {},
    "keyboard_baseline": {
        "normal_kpm": 120,
        "normal_backspace_ratio": 0.08,
        "normal_flight_mean": 0.18,
        "normal_flight_std": 0.06,
        "normal_pause_count": 4,
    },
    "implicit_patterns": {
        "high_completion_descriptions": [],
        "frequent_skip_descriptions": [],
    },
}


def ensure_user_profile(db: Session) -> dict:
    row = db.query(UserProfile).filter(UserProfile.id == 1).first()
    if row is None:
        row = UserProfile(id=1, profile_json=json.dumps(DEFAULT_PROFILE, ensure_ascii=False))
        db.add(row)
        db.commit()
        db.refresh(row)
    return _loads_profile(row.profile_json)


def get_user_profile(db: Session) -> dict:
    return ensure_user_profile(db)


def maybe_reflect_profile(db: Session) -> None:
    completed_count = (
        db.query(PlaySession).filter(PlaySession.completion_rate.is_not(None)).count()
    )
    if completed_count == 0 or completed_count % 10 != 0:
        return
    if not settings.openai_api_key:
        return

    row = db.query(UserProfile).filter(UserProfile.id == 1).first()
    if row is None:
        ensure_user_profile(db)
        row = db.query(UserProfile).filter(UserProfile.id == 1).first()
    if row is None:
        return

    sessions = (
        db.query(PlaySession)
        .filter(PlaySession.completion_rate.is_not(None))
        .order_by(PlaySession.timestamp.desc())
        .limit(30)
        .all()
    )
    patch = _reflect_with_llm(_loads_profile(row.profile_json), sessions)
    profile = _merge_profile(_loads_profile(row.profile_json), patch)
    row.profile_json = json.dumps(profile, ensure_ascii=False)
    row.updated_at = datetime.now()
    db.commit()


def _reflect_with_llm(profile: dict, sessions: list[PlaySession]) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    session_payload = [_session_to_reflection_payload(session) for session in sessions]
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "只根据稳定模式更新用户音乐画像。不要因为单次播放做强结论。"
                    "键盘状态只能作为 high_focus/high_stress/fatigue/stability 等工作状态弱信号，"
                    "不要把它总结成愤怒、难过等情绪。"
                    "输出 JSON patch，可包含 global_likes/global_dislikes/"
                    "scene_preferences/implicit_patterns/keyboard_baseline。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"current_profile": profile, "sessions": session_payload},
                    ensure_ascii=False,
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    return json.loads(response.choices[0].message.content or "{}")


def _session_to_reflection_payload(session: PlaySession) -> dict:
    return {
        "retrieval_query": session.retrieval_query,
        "completion_rate": session.completion_rate,
        "ended_reason": session.ended_reason,
        "keyboard_state": _loads_json(session.keyboard_state_json, {}),
        "keyboard_features": _loads_json(session.keyboard_features_json, {}),
        "playlist": _loads_json(session.playlist_json, []),
    }


def _merge_profile(profile: dict, patch: dict) -> dict:
    merged = dict(DEFAULT_PROFILE)
    merged.update(profile or {})
    for key, value in (patch or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key].update(value)
        else:
            merged[key] = value
    return merged


def _loads_profile(raw: str) -> dict:
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        payload = {}
    merged = dict(DEFAULT_PROFILE)
    merged.update(payload)
    return merged


def _loads_json(raw: str, default):
    try:
        return json.loads(raw or "")
    except json.JSONDecodeError:
        return default
