"""记忆服务。

Memory 是 EchoPet 的"长期记忆雏形"。

它记录：
    - 用户当时几点
    - 正在用什么软件
    - 情绪是什么
    - 推荐了哪首歌

当前版本已经删掉用户反馈模块。
Memory 现在只保留“推荐发生过”的历史记录，方便调试和后续扩展。
"""

from datetime import datetime

from sqlalchemy.orm import Session

from backend.models.schemas import ContextModel, EmotionResult, MemoryEntry
from backend.models.tables import Memory


def save_memory(
    db: Session,
    context: ContextModel,
    emotion: EmotionResult,
    song_id: str,
) -> Memory:
    """保存一次推荐记忆。

    调用位置：
        `/api/analyze` 每次成功推荐歌曲后都会调用。

    参数：
        db:
            数据库会话。

        context:
            当前环境上下文。

        emotion:
            情绪分析结果。

        song_id:
            这次推荐的歌曲 ID。
    """

    entry = Memory(
        timestamp=datetime.now(),
        hour=context.hour,
        active_app=context.active_app,
        kpm=context.kpm,
        backspace_ratio=context.backspace_ratio,
        emotion=emotion.emotion,
        energy=emotion.energy,
        need=emotion.need,
        song_id=song_id,
    )

    # add: 把对象加入当前数据库会话。
    db.add(entry)

    # commit: 真正写入数据库。
    db.commit()

    # refresh: 让 entry 拿到数据库生成的字段，比如自增 id。
    db.refresh(entry)
    return entry


def list_memories(db: Session, limit: int, offset: int) -> tuple[list[Memory], int]:
    """分页查询记忆。

    参数：
        limit:
            返回多少条。

        offset:
            跳过多少条。

    返回：
        (entries, total)
        - entries: 当前页的数据
        - total: 总条数
    """

    total = db.query(Memory).count()
    entries = (
        db.query(Memory)
        .order_by(Memory.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return entries, total


def memory_to_response(entry: Memory) -> MemoryEntry:
    """把数据库 Memory 对象转换成接口响应 MemoryEntry。

    为什么要转换：
        数据库表是扁平字段：
            hour, active_app, emotion, energy...

        接口文档希望返回嵌套结构：
            context: { hour, active_app, ... }
            emotion: { emotion, energy, need }

    这个函数就是做结构整理。
    """

    return MemoryEntry(
        timestamp=entry.timestamp,
        context=ContextModel(
            hour=entry.hour,
            active_app=entry.active_app,
            kpm=entry.kpm,
            backspace_ratio=entry.backspace_ratio,
        ),
        emotion=EmotionResult(
            emotion=entry.emotion,
            energy=entry.energy,
            need=entry.need,
        ),
        song_id=entry.song_id,
    )
