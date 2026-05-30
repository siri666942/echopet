"""Embedding 推荐器。"""

import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.models.schemas import ContextModel
from backend.models.tables import PlaySession, Song
from backend.services.embedding_service import cosine_similarity, embed_text
from backend.services.serialization import parse_dict


def recommend_playlist(
    db: Session,
    retrieval_query: str,
    context: ContextModel,
    user_profile: dict,
    top_k: int = 5,
    recall_k: int = 20,
) -> list[Song]:
    query_embedding = embed_text(retrieval_query)
    candidates: list[tuple[float, Song]] = []

    for song in db.query(Song).all():
        try:
            song_embedding = json.loads(song.embedding or "[]")
        except json.JSONDecodeError:
            song_embedding = []
        if not song_embedding:
            continue

        semantic_score = cosine_similarity(query_embedding, song_embedding)
        feedback_score = calc_feedback_score(song)
        profile_score = calc_profile_score(song, user_profile)
        repeat_penalty = calc_recent_repeat_penalty(db, song)

        final_score = (
            semantic_score * 0.65
            + feedback_score * 0.20
            + profile_score * 0.10
            - repeat_penalty * 0.05
        )
        candidates.append((final_score, song))

    candidates.sort(key=lambda item: item[0], reverse=True)
    recalled = candidates[:recall_k]
    return [song for _, song in recalled[:top_k]]


def calc_feedback_score(song: Song) -> float:
    completion = song.avg_completion_rate or 0.0
    skip_penalty = min((song.skip_count or 0) * 0.05, 0.5)
    play_bonus = min((song.play_count or 0) * 0.01, 0.1)
    return max(0.0, min(1.0, completion + play_bonus - skip_penalty))


def calc_profile_score(song: Song, user_profile: dict) -> float:
    description = (song.description or "").lower()
    semantic = parse_dict(song.semantic_features)
    likes = user_profile.get("global_likes", [])
    dislikes = user_profile.get("global_dislikes", [])
    implicit = user_profile.get("implicit_patterns", {})
    high_completion = implicit.get("high_completion_descriptions", [])
    frequent_skip = implicit.get("frequent_skip_descriptions", [])

    score = 0.0
    for term in likes + high_completion:
        if str(term).lower() in description or str(term).lower() in json.dumps(semantic, ensure_ascii=False).lower():
            score += 0.15
    for term in dislikes + frequent_skip:
        if str(term).lower() in description:
            score -= 0.15
    return max(-1.0, min(1.0, score))


def calc_recent_repeat_penalty(db: Session, song: Song) -> float:
    cutoff = datetime.now() - timedelta(hours=2)
    recent = (
        db.query(PlaySession)
        .filter(PlaySession.song_id == song.id, PlaySession.timestamp >= cutoff)
        .count()
    )
    return min(float(recent) * 0.2, 1.0)
