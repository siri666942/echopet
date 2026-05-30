"""`POST /api/feedback` 用户反馈接口。

用户听到推荐歌曲后，前端可以把反馈发到这里：

- positive: 喜欢
- negative: 不喜欢
- too_quiet: 太安静
- too_sad: 太悲伤
- more_energy: 想更有力量

这个接口的作用是让后端“记住偏好”。
以后推荐器会优先考虑相似场景下用户点过 positive 的歌曲。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.schemas import FeedbackRequest, FeedbackResponse
from backend.services.memory_service import apply_feedback
from backend.services.music_service import get_song_by_id


router = APIRouter(prefix="/api", tags=["feedback"])


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(req: FeedbackRequest, db: Session = Depends(get_db)) -> FeedbackResponse:
    """记录用户对某首歌的反馈。

    参数：
        req:
            请求体，包含：
            - song_id: 用户反馈的是哪首歌
            - feedback: 用户反馈类型

        db:
            数据库会话，由 FastAPI 自动注入。

    逻辑：
        1. 先检查 song_id 是否真的存在。
        2. 如果不存在，返回 404。
        3. 如果存在，就更新最近一次该歌曲的 memory 记录。
    """

    if get_song_by_id(db, req.song_id) is None:
        raise HTTPException(status_code=404, detail="song_id does not exist")

    apply_feedback(db, req.song_id, req.feedback)
    return FeedbackResponse()
