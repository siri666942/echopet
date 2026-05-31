"""播放会话服务。"""

import json
import uuid

from sqlalchemy.orm import Session

from backend.models.schemas import ContextModel
from backend.models.tables import PlaySession, Song
from backend.services import profile_service
from backend.services.serialization import song_to_response


def create_play_session(
    db: Session,
    user_text: str,
    retrieval_query: str,
    context: ContextModel,
    keyboard_features: dict | None,
    keyboard_state: dict | None,
    user_profile_snapshot: dict,
    song_id: str,
    playlist: list[Song],
) -> str:
    session_id = uuid.uuid4().hex
    entry = PlaySession(
        id=session_id,
        user_text=user_text,
        retrieval_query=retrieval_query,
        context_json=json.dumps(context.model_dump(), ensure_ascii=False),
        keyboard_features_json=json.dumps(keyboard_features or {}, ensure_ascii=False),
        keyboard_state_json=json.dumps(keyboard_state or {}, ensure_ascii=False),
        user_profile_snapshot=json.dumps(user_profile_snapshot, ensure_ascii=False),
        song_id=song_id,
        playlist_json=json.dumps(
            [song_to_response(song).model_dump() for song in playlist],
            ensure_ascii=False,
        ),
    )
    db.add(entry)
    db.commit()
    return session_id


def record_player_event(
    db: Session,
    session_id: str,
    completion_rate: float,
    ended_reason: str,
) -> PlaySession | None:
    session = db.query(PlaySession).filter(PlaySession.id == session_id).first()
    if session is None:
        return None

    session.completion_rate = completion_rate
    session.ended_reason = ended_reason

    song = db.query(Song).filter(Song.id == session.song_id).first()
    if song is not None:
        previous_count = song.play_count or 0
        previous_avg = song.avg_completion_rate or 0.0
        new_count = previous_count + 1
        song.play_count = new_count
        song.avg_completion_rate = ((previous_avg * previous_count) + completion_rate) / new_count
        if ended_reason == "skipped" or completion_rate < 0.25:
            song.skip_count = (song.skip_count or 0) + 1

    db.commit()
    db.refresh(session)
    profile_service.maybe_reflect_profile(db)
    return session
