"""`POST /api/transcribe` 语音转文本接口。

前端录音后，把音频转成 Base64 字符串发给这个接口。
后端会尝试用 faster-whisper 把音频转成文字。

注意：
    如果本机没有 faster-whisper 模型或依赖不可用，服务不会崩。
    它会返回空 transcript，让前端流程至少能跑下去。
"""

from fastapi import APIRouter

from backend.models.schemas import TranscribeRequest, TranscribeResponse
from backend.services.whisper_service import transcribe as transcribe_audio


router = APIRouter(prefix="/api", tags=["transcribe"])


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(req: TranscribeRequest) -> TranscribeResponse:
    """把 Base64 音频转成文本。

    参数：
        req.audio:
            音频文件内容的 Base64 字符串。

        req.audio_format:
            音频格式，比如 wav/mp3。默认 wav。

    返回：
        - transcript: 识别出的文本
        - language: 识别语言，默认 zh
        - source: 固定 faster-whisper
    """

    result = await transcribe_audio(req.audio, req.audio_format)
    return TranscribeResponse(**result)
