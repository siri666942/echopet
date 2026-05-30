"""`POST /api/analyze` 2.0 主链路。

新流程：
    text + context -> 用户画像 -> 音乐检索意图 -> embedding playlist -> 播放第一首 -> 创建 PlaySession
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.schemas import AnalyzeRequest, AnalyzeResponse, EmotionResult
from backend.services import intent_service, player_service, playlist_service, recommender
from backend.services.embedding_service import EmbeddingUnavailableError
from backend.services.memory_service import save_memory
from backend.services.play_session_service import create_play_session
from backend.services.profile_service import get_user_profile
from backend.services.serialization import song_to_response


router = APIRouter(prefix="/api", tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)) -> AnalyzeResponse:
    profile = get_user_profile(db)
    intent = await intent_service.build_music_intent(
        text=req.text,
        context=req.context,
        user_profile=profile,
    )

    try:
        playlist = recommender.recommend_playlist(
            db=db,
            retrieval_query=intent["retrieval_query"],
            context=req.context,
            user_profile=profile,
            top_k=5,
        )
    except EmbeddingUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="需要配置真实 embedding API：OPENAI_API_KEY / OPENAI_BASE_URL / EMBEDDING_MODEL",
        ) from exc

    if not playlist:
        raise HTTPException(
            status_code=404,
            detail="没有可推荐歌曲：请放入本地音乐，并确保歌曲已生成真实 embedding",
        )

    song = playlist[0]
    playlist_service.set_playlist(playlist)
    session_id = create_play_session(
        db=db,
        user_text=req.text,
        retrieval_query=intent["retrieval_query"],
        context=req.context,
        user_profile_snapshot=profile,
        song_id=song.id,
        playlist=playlist,
    )
    player_status = player_service.play(song.file_path, song.id, song.title, song.artist)

    emotion = EmotionResult(**intent["emotion_compat"])
    save_memory(db, req.context, emotion, song.id)

    return AnalyzeResponse(
        transcript=req.text.strip(),
        emotion=emotion,
        current_state=intent["current_state"],
        bubble_text=intent["bubble_text"],
        assistant_reply=intent["assistant_reply"],
        recommendation=song_to_response(song),
        play_action="play",
        player_status=player_status,
        session_id=session_id,
        retrieval_query=intent["retrieval_query"],
        playlist=[song_to_response(item) for item in playlist],
    )
