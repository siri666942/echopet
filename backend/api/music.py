"""`GET /api/music/random` 随机歌曲接口。

这个接口用于从 songs 表里随机拿一首歌。

用途：
    - 前端调试曲库是否可用。
    - 后续也可以用于“随便来一首”的功能。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.schemas import SongResponse
from backend.services.music_service import get_random_song
from backend.services.serialization import song_to_response


router = APIRouter(prefix="/api", tags=["music"])


@router.get("/music/random", response_model=SongResponse)
async def random_music(db: Session = Depends(get_db)) -> SongResponse:
    """随机返回一首歌曲。

    参数：
        db:
            数据库会话，由 FastAPI 自动注入。

    返回：
        SongResponse，字段包括 id/title/artist/tags/energy/mood/file_path。
    """

    song = get_random_song(db)
    if song is None:
        raise HTTPException(status_code=404, detail="Music library is empty")
    return song_to_response(song)
