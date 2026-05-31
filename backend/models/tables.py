"""数据库表定义。

这里放的是 SQLAlchemy ORM 表模型：它描述 SQLite 里真实有哪些表、字段和默认值。
接口 JSON 模型在 `schemas.py`，不要把这两类模型混在一起。
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.database import Base


class Song(Base):
    """歌曲表。

    旧字段 `tags/energy/mood` 继续保留，保证旧前端字段不炸。
    但 2.0 推荐主链路使用 `description + embedding + 隐式反馈统计`。
    """

    __tablename__ = "songs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    artist: Mapped[str] = mapped_column(String, default="Unknown")
    file_path: Mapped[str] = mapped_column(String, nullable=False)

    tags: Mapped[str] = mapped_column(Text, default="[]")
    energy: Mapped[float] = mapped_column(Float, default=0.5)
    mood: Mapped[str] = mapped_column(String, default="neutral")

    description: Mapped[str] = mapped_column(Text, default="")
    audio_features: Mapped[str] = mapped_column(Text, default="{}")
    semantic_features: Mapped[str] = mapped_column(Text, default="{}")
    embedding: Mapped[str] = mapped_column(Text, default="[]")

    play_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_completion_rate: Mapped[float] = mapped_column(Float, default=0.0)
    skip_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Memory(Base):
    """兼容保留的推荐记忆表。

    2.0 的长期学习主表是 PlaySession + UserProfile。
    Memory 只作为旧接口 `/api/memory` 的简单历史记录。
    """

    __tablename__ = "memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    hour: Mapped[int] = mapped_column(Integer)
    active_app: Mapped[str] = mapped_column(String)
    kpm: Mapped[int] = mapped_column(Integer, default=0)
    backspace_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    emotion: Mapped[str] = mapped_column(String)
    energy: Mapped[float] = mapped_column(Float)
    need: Mapped[str] = mapped_column(String, default="companionship")
    song_id: Mapped[str] = mapped_column(String)


class PlaySession(Base):
    """一次播放会话。

    `/api/analyze` 创建 session，`/api/player/event` 回填完成率和结束原因。
    这张表是隐式反馈的原始事件日志。
    """

    __tablename__ = "play_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user_text: Mapped[str] = mapped_column(Text, default="")
    retrieval_query: Mapped[str] = mapped_column(Text, default="")
    context_json: Mapped[str] = mapped_column(Text, default="{}")
    keyboard_features_json: Mapped[str] = mapped_column(Text, default="{}")
    keyboard_state_json: Mapped[str] = mapped_column(Text, default="{}")
    user_profile_snapshot: Mapped[str] = mapped_column(Text, default="{}")

    song_id: Mapped[str] = mapped_column(String, nullable=False)
    playlist_json: Mapped[str] = mapped_column(Text, default="[]")

    completion_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    ended_reason: Mapped[str | None] = mapped_column(String, nullable=True)


class UserProfile(Base):
    """长期用户画像。

    目前只做单用户本地 MVP，所以表里通常只有 id=1 一行。
    """

    __tablename__ = "user_profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class SongIngestFailure(Base):
    """歌曲入库失败记录。

    Essentia 分析失败时不能写默认特征假装入库成功，所以用这张表留下失败原因。
    """

    __tablename__ = "song_ingest_failures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
