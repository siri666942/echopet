"""`GET /api/memory` 历史记忆接口。

memory 表存的是：

    “什么时间、什么环境、什么情绪、推荐了哪首歌、用户反馈是什么”

这个接口用于查看历史记录，也方便后面做调试。
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.schemas import MemoryResponse
from backend.services.memory_service import list_memories, memory_to_response


router = APIRouter(prefix="/api", tags=["memory"])


@router.get("/memory", response_model=MemoryResponse)
async def memory(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> MemoryResponse:
    """分页返回历史记忆。

    参数：
        limit:
            最多返回多少条。默认 20，最小 1，最大 100。

        offset:
            从第几条开始跳过。默认 0。
            例如 limit=20, offset=40，就是取第 41 到 60 条。

        db:
            数据库会话，由 FastAPI 自动注入。

    返回：
        - entries: 当前页的记忆条目
        - total: 数据库里总共有多少条 memory
    """

    entries, total = list_memories(db, limit=limit, offset=offset)

    # 数据库对象 Memory 不能直接返回给前端。
    # memory_to_response 会把扁平字段重新组装成接口文档里的嵌套结构：
    # context: {...}
    # emotion: {...}
    return MemoryResponse(entries=[memory_to_response(entry) for entry in entries], total=total)
