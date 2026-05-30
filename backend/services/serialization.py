"""数据库对象到接口响应对象的转换。"""

import json

from backend.models.schemas import SongResponse
from backend.models.tables import Song


def parse_json(raw: str | None, fallback):
    if not raw:
        return fallback
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return fallback
    return parsed


def parse_tags(raw_tags: str | None) -> list[str]:
    parsed = parse_json(raw_tags, [])
    return parsed if isinstance(parsed, list) else []


def parse_dict(raw: str | None) -> dict:
    parsed = parse_json(raw, {})
    return parsed if isinstance(parsed, dict) else {}


def song_to_response(song: Song) -> SongResponse:
    return SongResponse(
        id=song.id,
        title=song.title,
        artist=song.artist,
        tags=parse_tags(song.tags),
        energy=song.energy,
        mood=song.mood,
        file_path=song.file_path,
        description=song.description,
        audio_features=parse_dict(song.audio_features),
        semantic_features=parse_dict(song.semantic_features),
        play_count=song.play_count or 0,
        avg_completion_rate=song.avg_completion_rate or 0.0,
    )
