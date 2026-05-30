"""接口请求/响应模型。

这里的模型是 Pydantic 模型。

它们的作用：

1. 校验前端传来的 JSON
   - 比如 hour 必须 0 到 23
   - feedback 只能是 positive/negative/too_quiet/too_sad/more_energy

2. 规范后端返回给前端的 JSON
   - FastAPI 会根据 response_model 自动检查返回值。
   - Swagger 文档也会根据这些模型自动生成。

一句话：
    schemas.py 管“接口长什么样”，tables.py 管“数据库长什么样”。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# Literal 的意思是：这个字段只能取下面列出来的值。
# 如果前端传了别的值，FastAPI 会直接返回 422。
EmotionName = Literal["frustrated", "sad", "happy", "focused", "tired", "anxious", "calm"]
NeedName = Literal["comfort", "focus", "energy", "relaxation", "companionship"]
InputSource = Literal["text", "faster_whisper"]
FeedbackValue = Literal["positive", "negative", "too_quiet", "too_sad", "more_energy"]
PlayerState = Literal["idle", "loading", "playing", "paused", "error"]
PetState = Literal["idle", "focus", "tired", "frustrated", "sad"]
PlayAction = Literal["play", "pause", "skip", "none"]


class ContextModel(BaseModel):
    """环境上下文。

    前端调用 `/api/analyze` 时要传这个。
    后端调用 `/api/context` 时也返回这个。
    """

    # 当前小时，0 到 23。
    hour: int = Field(ge=0, le=23)

    # 当前活跃应用，比如 VSCode、Chrome、Unknown。
    active_app: str = Field(min_length=1)

    # 每分钟按键数。MVP 阶段后端返回 0，也允许前端传真实值。
    kpm: int = Field(ge=0)

    # 退格键比例，0 到 1。
    backspace_ratio: float = Field(ge=0.0, le=1.0)


class TranscribeRequest(BaseModel):
    """`POST /api/transcribe` 请求体。"""

    # 音频文件的 Base64 字符串。
    audio: str = Field(min_length=1)

    # 音频格式，默认 wav。
    audio_format: str = "wav"


class AnalyzeRequest(BaseModel):
    """`POST /api/analyze` 请求体。"""

    # 用户说的话。
    text: str = Field(min_length=1)

    # 输入来源：直接文字，或者 faster-whisper 转写结果。
    input_source: InputSource

    # 当前环境。
    context: ContextModel


class FeedbackRequest(BaseModel):
    """`POST /api/feedback` 请求体。"""

    # 用户反馈的是哪首歌。
    song_id: str = Field(min_length=1)

    # 反馈类型。
    feedback: FeedbackValue


class TranscribeResponse(BaseModel):
    """`POST /api/transcribe` 响应体。"""

    transcript: str
    language: str = "zh"
    source: str = "faster-whisper"


class EmotionResult(BaseModel):
    """情绪分析结果。"""

    # 情绪标签。
    emotion: EmotionName

    # 能量值，0 到 1。
    energy: float = Field(ge=0.0, le=1.0)

    # 当前最需要的东西，例如安抚、专注、陪伴。
    need: NeedName


class SongResponse(BaseModel):
    """返回给前端的歌曲结构。"""

    id: str
    title: str
    artist: str
    tags: list[str]
    energy: float
    mood: str
    file_path: str


class AnalyzeResponse(BaseModel):
    """`POST /api/analyze` 响应体。

    这是前端最主要使用的返回值。
    """

    transcript: str
    emotion: EmotionResult
    current_state: PetState
    bubble_text: str
    assistant_reply: str
    recommendation: SongResponse
    play_action: PlayAction
    player_status: PlayerState


class FeedbackResponse(BaseModel):
    """`POST /api/feedback` 响应体。"""

    status: str = "ok"
    message: str = "Feedback recorded"


class MemoryEntry(BaseModel):
    """返回给前端的一条记忆。"""

    timestamp: datetime
    context: ContextModel
    emotion: EmotionResult
    song_id: str
    feedback: str | None = None


class MemoryResponse(BaseModel):
    """`GET /api/memory` 响应体。"""

    entries: list[MemoryEntry]
    total: int


class PlayerStatusResponse(BaseModel):
    """`GET /api/player/status` 响应体。"""

    player: str = "mpv"
    status: PlayerState
    track_id: str | None = None
    title: str | None = None
    artist: str | None = None
