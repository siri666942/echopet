"""重新扫描并初始化本地曲库。

用途：
    docker compose exec echopet-backend python -m backend.scripts.reindex_music

默认不会删除旧 songs，只会重新扫描 MUSIC_DIR 并补全缺失特征。
如果明确传 `--reset`，才会清空 songs / song_ingest_failures 后完全重建。
如果 Essentia TensorFlow 模型路径或 embedding API 没配好，歌曲仍会失败；
失败原因会写入 song_ingest_failures。
"""

import argparse

from backend.models.database import SessionLocal, init_db
from backend.models.tables import Song, SongIngestFailure
from backend.services.music_service import initialize_library


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="清空旧曲库记录后重新扫描")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        if args.reset:
            db.query(Song).delete()
            db.query(SongIngestFailure).delete()
            db.commit()
        initialize_library(db)
        song_count = db.query(Song).count()
        failure_count = db.query(SongIngestFailure).count()
        print(f"songs={song_count}")
        print(f"failures={failure_count}")
        for failure in db.query(SongIngestFailure).order_by(SongIngestFailure.id.desc()).limit(10):
            print(f"FAIL {failure.file_path}: {failure.reason}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
