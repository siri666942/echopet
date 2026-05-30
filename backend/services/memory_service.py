"""记忆服务。

Memory 是 EchoPet 的“长期记忆雏形”。

它记录：
    - 用户当时几点
    - 正在用什么软件
    - 情绪是什么
    - 推荐了哪首歌
    - 用户后续喜不喜欢

推荐器会利用这些记录：
    “如果用户以前在相似场景喜欢过某首歌，下次优先推荐它。”
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
    feedback: str | None = None,
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

        feedback:
            用户反馈。刚推荐时通常还没有反馈，所以默认 None。
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
        feedback=feedback,
    )

    # add: 把对象加入当前数据库会话。
    db.add(entry)

    # commit: 真正写入数据库。
    db.commit()

    # refresh: 让 entry 拿到数据库生成的字段，比如自增 id。
    db.refresh(entry)
    return entry


def apply_feedback(db: Session, song_id: str, feedback: str) -> Memory:
    """把用户反馈写入记忆。

    参数：
        song_id:
            用户反馈的歌曲。

        feedback:
            positive / negative / too_quiet / too_sad / more_energy。

    逻辑：
        1. 找最近一次推荐过这首歌的 Memory。
        2. 如果找到了，就更新它的 feedback。
        3. 如果没找到，就创建一条简化 Memory，至少把反馈记下来。
    """

    entry = (
        db.query(Memory)
        .filter(Memory.song_id == song_id)
        .order_by(Memory.timestamp.desc())
        .first()
    )

    if entry is None:
        # 兜底逻辑：
        # 正常流程是 analyze 先保存 memory，feedback 后更新它。
        # 但如果前端直接调 feedback，也不要报错到无法记录。
        entry = Memory(
            timestamp=datetime.now(),
            hour=datetime.now().hour,
            active_app="Unknown",
            kpm=0,
            backspace_ratio=0.0,
            emotion="calm",
            energy=0.5,
            need="companionship",
            song_id=song_id,
            feedback=feedback,
        )
        db.add(entry)
    else:
        entry.feedback = feedback

    db.commit()
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
        feedback=entry.feedback,
    )
