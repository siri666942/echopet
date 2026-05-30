"""曲库管理服务。

这个文件负责 songs 表相关操作：

- 启动时扫描本地音乐目录
- 曲库为空时插入样例歌曲
- 随机拿一首歌
- 按 song_id 查询歌曲

注意：
    当前样例歌曲只是元数据，文件路径可能不真实存在。
    这样做是为了“没有本地 mp3 时也能演示接口”。
"""

import json
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.tables import Song


# 支持扫描入库的音频格式。
SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".flac"}

# 开发样例曲库。
# 当用户没有放任何音乐文件时，用它保证 /api/analyze 和 /api/music/random 能跑。
SAMPLE_SONGS = [
    {
        "id": "s001",
        "title": "Midnight Rain",
        "artist": "LoFi Dreams",
        "tags": ["lofi", "calm", "night"],
        "energy": 0.3,
        "mood": "soothing",
        "file_path": str(settings.music_dir / "s001.mp3"),
    },
    {
        "id": "s002",
        "title": "Deep Focus",
        "artist": "Ambient Works",
        "tags": ["ambient", "focus"],
        "energy": 0.5,
        "mood": "focused",
        "file_path": str(settings.music_dir / "s002.mp3"),
    },
    {
        "id": "s003",
        "title": "Sunrise Energy",
        "artist": "Morning Beats",
        "tags": ["upbeat", "morning"],
        "energy": 0.8,
        "mood": "energetic",
        "file_path": str(settings.music_dir / "s003.mp3"),
    },
]


def initialize_library(db: Session) -> None:
    """初始化曲库。

    调用位置：
        main.py 的 lifespan 启动阶段。

    步骤：
        1. 扫描 backend/music 目录，把真实音乐文件写入 songs 表。
        2. 如果 songs 表仍然为空，插入 SAMPLE_SONGS。
    """

    scan_music_dir(db)
    if db.query(Song).count() == 0:
        add_sample_songs(db)


def scan_music_dir(db: Session) -> None:
    """扫描本地音乐目录并入库。

    参数：
        db:
            数据库会话。

    逻辑：
        - 遍历 MUSIC_DIR 下面的文件
        - 只接受 .mp3/.wav/.flac
        - 已经入库过的文件不重复插入
        - 新文件默认 artist=Unknown、energy=0.5、mood=neutral
    """

    music_dir = Path(settings.music_dir)
    music_dir.mkdir(parents=True, exist_ok=True)

    # 先拿到数据库里已有的 file_path，用于去重。
    existing_paths = {Path(song.file_path).resolve() for song in db.query(Song).all()}
    next_index = db.query(Song).count() + 1

    for file_path in sorted(music_dir.iterdir()):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        resolved = file_path.resolve()
        if resolved in existing_paths:
            continue

        song = Song(
            id=_next_available_id(db, next_index),
            title=file_path.stem,
            artist="Unknown",
            tags=json.dumps(["local"], ensure_ascii=False),
            energy=0.5,
            mood="neutral",
            file_path=str(resolved),
        )
        db.add(song)
        next_index += 1

    db.commit()


def add_sample_songs(db: Session) -> None:
    """插入样例歌曲。

    这里用 db.merge 而不是 db.add。

    区别：
        - add: 如果主键已存在，可能报重复错误。
        - merge: 有就更新，没有就插入。

    所以重复启动服务也不会把样例歌插爆。
    """

    for sample in SAMPLE_SONGS:
        db.merge(
            Song(
                id=sample["id"],
                title=sample["title"],
                artist=sample["artist"],
                tags=json.dumps(sample["tags"], ensure_ascii=False),
                energy=sample["energy"],
                mood=sample["mood"],
                file_path=sample["file_path"],
            )
        )
    db.commit()


def get_random_song(db: Session) -> Song | None:
    """从 songs 表随机取一首歌。"""

    return db.query(Song).order_by(func.random()).first()


def get_song_by_id(db: Session, song_id: str) -> Song | None:
    """按歌曲 ID 查歌。

    参数：
        song_id:
            歌曲主键，比如 s001。
    """

    return db.query(Song).filter(Song.id == song_id).first()


def _next_available_id(db: Session, start: int) -> str:
    """生成一个没有被占用的歌曲 ID。

    参数：
        start:
            从哪个数字开始试。

    返回：
        形如 s001、s002、s003 的 ID。
    """

    index = start
    while True:
        song_id = f"s{index:03d}"
        if db.query(Song).filter(Song.id == song_id).first() is None:
            return song_id
        index += 1
