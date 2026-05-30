"""序列化工具。

“序列化”在这里的意思是：

    把数据库对象转换成适合返回给前端的 Pydantic 响应对象。

为什么需要这个文件：
    数据库 Song.tags 是 JSON 字符串；
    前端想要的是 list[str]。

所以这里集中处理这个转换，避免每个 API 都自己写一遍。
"""

import json

from backend.models.schemas import SongResponse
from backend.models.tables import Song


def parse_tags(raw_tags: str | None) -> list[str]:
    """把数据库里的 tags 字符串转成 Python 列表。

    参数：
        raw_tags:
            数据库里存的字符串，例如 '["lofi", "calm"]'。

    返回：
        list[str]。

    兜底：
        如果 tags 为空或 JSON 格式坏了，就返回 []。
    """

    if not raw_tags:
        return []
    try:
        parsed = json.loads(raw_tags)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def song_to_response(song: Song) -> SongResponse:
    """把数据库 Song 对象转成接口 SongResponse。

    参数：
        song:
            SQLAlchemy 的 Song ORM 对象。

    返回：
        Pydantic 的 SongResponse。
    """

    return SongResponse(
        id=song.id,
        title=song.title,
        artist=song.artist,
        tags=parse_tags(song.tags),
        energy=song.energy,
        mood=song.mood,
        file_path=song.file_path,
    )
