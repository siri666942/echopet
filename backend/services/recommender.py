"""歌曲推荐服务。

推荐器现在是一个简单但可解释的算法。

它主要看两件事：

1. 用户历史反馈
   - 如果用户在相似时间、相似应用里喜欢过某首歌，给它加分。

2. 能量值匹配
   - 情绪分析会给出 emotion.energy。
   - 歌曲也有 song.energy。
   - 两者越接近，越适合。

最后选分数最高的歌。
"""

from sqlalchemy.orm import Session

from backend.models.schemas import ContextModel, EmotionResult
from backend.models.tables import Memory, Song


def recommend(db: Session, emotion: EmotionResult, context: ContextModel) -> Song | None:
    """根据情绪和上下文推荐歌曲。

    参数：
        db:
            数据库会话。

        emotion:
            当前情绪分析结果。

        context:
            当前环境上下文。

    返回：
        Song 或 None。
        如果曲库为空，就返回 None。
    """

    # 相似时间：当前小时前后 2 小时。
    # 例如现在 23 点，就看 21、22、23。
    # 注意 range 右边不包含，所以 min(24, hour + 3)。
    hour_range = range(max(0, context.hour - 2), min(24, context.hour + 3))

    # 找历史上“相似时间 + 相同应用 + 用户点过 positive”的记忆。
    positive_memories = (
        db.query(Memory)
        .filter(
            Memory.hour.in_(hour_range),
            Memory.active_app == context.active_app,
            Memory.feedback == "positive",
        )
        .all()
    )

    # song_scores 记录历史偏好分。
    # 用户每在相似场景喜欢过一次这首歌，就 +1。
    song_scores: dict[str, float] = {}
    for memory in positive_memories:
        song_scores[memory.song_id] = song_scores.get(memory.song_id, 0.0) + 1.0

    songs = db.query(Song).all()
    if not songs:
        return None

    def score(song: Song) -> float:
        """计算单首歌得分。

        得分 = 历史偏好分 + 能量匹配分

        能量匹配分：
            `1.0 - abs(song.energy - emotion.energy)`

        例子：
            用户能量 0.3，歌曲能量 0.3 -> 1.0 分
            用户能量 0.3，歌曲能量 0.8 -> 0.5 分
        """

        energy_match = 1.0 - abs(song.energy - emotion.energy)
        return song_scores.get(song.id, 0.0) + energy_match

    return max(songs, key=score)
