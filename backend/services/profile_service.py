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
    session_payload = [
        {
            "retrieval_query": s.retrieval_query,
            "completion_rate": s.completion_rate,
            "ended_reason": s.ended_reason,
            "playlist": json.loads(s.playlist_json or "[]"),
        }
        for s in sessions
    ]
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "只根据稳定模式更新用户音乐画像。不要因为单次播放做强结论。"
                    "输出 JSON patch，可包含 global_likes/global_dislikes/"
                    "scene_preferences/implicit_patterns。"
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
