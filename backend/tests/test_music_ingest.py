"""测试曲库入库失败不会创建假歌曲。"""

from pathlib import Path

from backend.models.tables import Song, SongIngestFailure
from backend.services import music_service


def test_scan_music_dir_records_failure_without_song(db_session, tmp_path, monkeypatch):
    audio = tmp_path / "bad.mp3"
    audio.write_bytes(b"not real audio")

    monkeypatch.setattr(music_service.settings, "music_dir", tmp_path)

    def fail_extract(file_path: str):
        raise music_service.AudioFeatureExtractionError("essentia failed")

    monkeypatch.setattr(music_service, "extract_audio_features", fail_extract)

    before = db_session.query(Song).count()
    music_service.scan_music_dir(db_session)

    assert db_session.query(Song).count() == before
    failure = db_session.query(SongIngestFailure).filter(
        SongIngestFailure.file_path == str(Path(audio).resolve())
    ).first()
    assert failure is not None
    assert "essentia failed" in failure.reason
