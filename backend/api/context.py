"""`GET /api/context` 环境上下文接口。

这个接口给前端一个“当前用户环境”的快照。

当前返回：
    - hour: 当前小时，0 到 23
    - active_app: 当前活跃软件名，例如 VSCode / Chrome / Unknown
    - kpm: 每分钟按键数，MVP 先返回 0
    - backspace_ratio: 退格比例，MVP 先返回 0.0

前端一般会先调用这个接口，再调用 `/api/analyze`。
"""

from fastapi import APIRouter

from backend.models.schemas import ContextModel
from backend.services.context_service import get_current_context


router = APIRouter(prefix="/api", tags=["context"])


@router.get("/context", response_model=ContextModel)
async def context() -> ContextModel:
    """返回当前环境上下文。

    这里没有数据库参数，因为它只读当前系统环境，不需要查表。
    `ContextModel(**dict)` 的意思是：
        把 service 返回的字典塞进 Pydantic 模型里校验一遍。
    """

    return ContextModel(**get_current_context())
