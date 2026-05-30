"""`GET /api/player/status` 播放器状态接口。

前端需要知道后端现在有没有在播歌，正在播哪首。

这个接口不直接控制播放器，只查询 `player_service` 里维护的当前状态。
"""

from fastapi import APIRouter

from backend.models.schemas import PlayerStatusResponse
from backend.services import player_service


router = APIRouter(prefix="/api", tags=["player"])


@router.get("/player/status", response_model=PlayerStatusResponse)
async def player_status() -> PlayerStatusResponse:
    """返回当前播放器状态。

    可能的 status：
        - idle: 空闲
        - loading: 正在准备播放
        - playing: 正在播放
        - paused: 暂停
        - error: 播放失败，例如没安装 mpv
    """

    return PlayerStatusResponse(**player_service.get_status())
