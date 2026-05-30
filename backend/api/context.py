"""GET /api/context 环境上下文接口。

后端负责采集 hour 和 active_app。
kpm 和 backspace_ratio 由前端采集后通过 query 参数传入。
"""

from fastapi import APIRouter

from backend.models.schemas import ContextModel
from backend.services.context_service import get_current_context


router = APIRouter(prefix="/api", tags=["context"])


@router.get("/context", response_model=ContextModel)
async def context(
    kpm: int = 0,
    backspace_ratio: float = 0.0,
) -> ContextModel:
    """返回当前环境上下文。

    Query 参数：
        kpm: 前端采集的每分钟按键数，默认 0。
        backspace_ratio: 前端采集的退格键比例，默认 0.0。
    """

    return ContextModel(**get_current_context(kpm=kpm, backspace_ratio=backspace_ratio))
