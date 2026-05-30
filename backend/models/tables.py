"""数据库表定义。

这里定义的是“数据库里实际存什么字段”。

注意区分：

- `tables.py`
  - SQLAlchemy ORM 模型
  - 对应 SQLite 里的真实表
  - 用于数据库读写

- `schemas.py`
  - Pydantic 模型
  - 对应接口请求/响应格式
  - 用于校验前端传来的 JSON，以及规范返回给前端的 JSON
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.database import Base


class Song(Base):
    """歌曲表。

    一行 Song 就是一首歌。
    推荐器会从这个表里挑歌。
    """

    __tablename__ = "songs"

    # 歌曲 ID，例如 s001。
    id: Mapped[str] = mapped_column(String, primary_key=True)

    # 歌名，例如 Midnight Rain。
    title: Mapped[str] = mapped_column(String, nullable=False)

    # 艺术家名。
    artist: Mapped[str] = mapped_column(String, nullable=False)

    # 标签。
    # SQLite 没有原生 list 类型，所以这里用 JSON 字符串存：
    #   '["lofi", "calm", "night"]'
    # 返回给前端时，serialization.py 会把它转回 list[str]。
    tags: Mapped[str] = mapped_column(Text, default="[]")

    # 歌曲能量值，0 到 1。
    # 低能量：舒缓、安静。
    # 高能量：更振奋。
    energy: Mapped[float] = mapped_column(Float, default=0.5)

    # 情绪风格，例如 soothing / focused / energetic。
    mood: Mapped[str] = mapped_column(String, default="neutral")

    # 本地文件路径。
    # mpv 播放时靠这个路径找到音频文件。
    file_path: Mapped[str] = mapped_column(String, nullable=False)


class Memory(Base):
    """记忆表。

    一行 Memory 记录一次推荐上下文：

        用户当时是什么环境 -> 后端判断是什么情绪 -> 推荐了哪首歌 -> 用户反馈如何

    推荐器以后会用这些历史记录调整推荐。
    """

    __tablename__ = "memory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 这次推荐发生的时间。
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # 以下字段来自 ContextModel。
    hour: Mapped[int] = mapped_column(Integer)
    active_app: Mapped[str] = mapped_column(String)
    kpm: Mapped[int] = mapped_column(Integer, default=0)
    backspace_ratio: Mapped[float] = mapped_column(Float, default=0.0)

    # 以下字段来自 EmotionResult。
    emotion: Mapped[str] = mapped_column(String)
    energy: Mapped[float] = mapped_column(Float)
    need: Mapped[str] = mapped_column(String, default="companionship")

    # 当时推荐的歌曲。
    song_id: Mapped[str] = mapped_column(String)

    # 用户反馈。
    # 刚 analyze 完还没有反馈，所以允许为空。
    feedback: Mapped[str | None] = mapped_column(String, nullable=True)
