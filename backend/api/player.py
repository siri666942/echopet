"""播放器相关接口。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.schemas import (
    PlayerEventRequest,
    PlayerEventResponse,
    PlayerStatusResponse,
)
from backend.services import player_service
from backend.services.play_session_service import record_player_event


router = APIRouter(prefix="/api", tags=["player"])


@router.get("/player/status", response_model=PlayerStatusResponse)
async def player_status() -> PlayerStatusResponse:
    return PlayerStatusResponse(**player_service.get_status())


@router.post("/player/event", response_model=PlayerEventResponse)
async def player_event(
    req: PlayerEventRequest,
    db: Session = Depends(get_db),
) -> PlayerEventResponse:
    session = record_player_event(
        db=db,
        session_id=req.session_id,
        completion_rate=req.completion_rate,
        ended_reason=req.ended_reason,
    )
    if session is None:
        raise HTTPException(status_code=404, detail="session_id does not exist")
    return PlayerEventResponse()
