"""曲库扫描、入库和特征补全。

新歌必须经过 Essentia 分析。分析失败时记录 SongIngestFailure，不写 Song。
"""

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.tables import Song, SongIngestFailure
from backend.services.audio_feature_service import (
    AudioFeatureExtractionError,
    extract_audio_features,
)
from backend.services.embedding_service import embed_text
from backend.services.song_description_service import build_song_description


SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".flac"}


def initialize_library(db: Session) -> None:
    scan_music_dir(db)
    backfill_song_features(db)


def scan_music_dir(db: Session) -> None:
    music_dir = Path(settings.music_dir)
    music_dir.mkdir(parents=True, exist_ok=True)

    existing_paths = {Path(song.file_path).resolve() for song in db.query(Song).all()}
    next_index = db.query(Song).count() + 1

    for file_path in sorted(music_dir.iterdir()):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        resolved = file_path.resolve()
        if resolved in existing_paths:
            continue

        try:
            song = _build_song_from_file(db, resolved, next_index)
        except Exception as exc:
            _record_ingest_failure(db, str(resolved), str(exc))
            continue

        db.add(song)
        db.commit()
        next_index += 1


def backfill_song_features(db: Session) -> None:
    for song in db.query(Song).all():
        changed = False
        file_path = Path(song.file_path)
        if not file_path.exists():
            _record_ingest_failure(db, song.file_path, "file not found during backfill")
            continue

        needs_features = (
            not song.audio_features
            or song.audio_features == "{}"
            or not song.semantic_features
            or song.semantic_features == "{}"
        )

        if needs_features:
            try:
                features = extract_audio_features(song.file_path)
            except AudioFeatureExtractionError as exc:
                _record_ingest_failure(db, song.file_path, str(exc))
                continue

            song.audio_features = json.dumps(features["basic"], ensure_ascii=False)
            song.semantic_features = json.dumps(features["semantic"], ensure_ascii=False)
            song.energy = _legacy_energy_from_essentia(features)
            song.mood = _legacy_mood_from_essentia(features)
            song.tags = json.dumps(_legacy_tags_from_essentia(features), ensure_ascii=False)
            changed = True
        else:
            features = {
                "basic": _loads_dict(song.audio_features),
                "semantic": _loads_dict(song.semantic_features),
            }

        if not song.description:
            song.description = build_song_description(song.title, features)
            changed = True

        if not song.embedding or song.embedding == "[]":
            try:
                song.embedding = json.dumps(embed_text(song.description))
                changed = True
            except Exception as exc:
                _record_ingest_failure(db, song.file_path, f"embedding failed: {exc}")
                continue

        if changed:
            song.updated_at = datetime.now()
            db.commit()


def get_random_song(db: Session) -> Song | None:
    return db.query(Song).order_by(func.random()).first()


def get_song_by_id(db: Session, song_id: str) -> Song | None:
    return db.query(Song).filter(Song.id == song_id).first()


def _build_song_from_file(db: Session, file_path: Path, next_index: int) -> Song:
    features = extract_audio_features(str(file_path))
    description = build_song_description(file_path.stem, features)
    embedding = embed_text(description)
    now = datetime.now()

    return Song(
        id=_next_available_id(db, next_index),
        title=file_path.stem,
        artist="Unknown",
        file_path=str(file_path),
        tags=json.dumps(_legacy_tags_from_essentia(features), ensure_ascii=False),
        energy=_legacy_energy_from_essentia(features),
        mood=_legacy_mood_from_essentia(features),
        description=description,
        audio_features=json.dumps(features["basic"], ensure_ascii=False),
        semantic_features=json.dumps(features["semantic"], ensure_ascii=False),
        embedding=json.dumps(embedding),
        created_at=now,
        updated_at=now,
    )


def _legacy_energy_from_essentia(features: dict) -> float:
    basic = features.get("basic", {})
    loudness = min(max(float(basic.get("loudness") or 0.0), 0.0), 1.0)
    danceability = min(max(float(basic.get("danceability") or 0.0) / 3.0, 0.0), 1.0)
    return round((loudness * 0.6) + (danceability * 0.4), 3)


def _legacy_mood_from_essentia(features: dict) -> str:
    semantic = features.get("semantic", {})
    mood = semantic.get("mood")
    if isinstance(mood, dict):
        raw = mood.get("raw")
        if isinstance(raw, dict) and raw:
            return str(max(raw.items(), key=lambda item: item[1])[0])
    arousal = semantic.get("arousal")
    valence = semantic.get("valence")
    if isinstance(arousal, (int, float)) and isinstance(valence, (int, float)):
        if arousal > 0.6 and valence > 0.5:
            return "energetic"
        if arousal < 0.4:
            return "calm"
    return "essentia_analyzed"


def _legacy_tags_from_essentia(features: dict) -> list[str]:
    tags = ["essentia"]
    semantic = features.get("semantic", {})
    genre = semantic.get("genre")
    if isinstance(genre, dict):
        raw = genre.get("raw")
        if isinstance(raw, dict) and raw:
            tags.append(str(max(raw.items(), key=lambda item: item[1])[0]))
    voice = semantic.get("voice_instrumental")
    if isinstance(voice, dict):
        tags.append("voice_instrumental")
    return tags


def _record_ingest_failure(db: Session, file_path: str, reason: str) -> None:
    db.add(SongIngestFailure(file_path=file_path, reason=reason))
    db.commit()


def _loads_dict(raw: str | None) -> dict:
    try:
        parsed = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _next_available_id(db: Session, start: int) -> str:
    index = start
    while True:
        song_id = f"s{index:03d}"
        if db.query(Song).filter(Song.id == song_id).first() is None:
            return song_id
        index += 1
