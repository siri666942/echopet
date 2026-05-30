"""Pydantic 请求/响应模型。

这些模型定义前端传什么 JSON、后端回什么 JSON。数据库表定义在 `tables.py`。
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


EmotionName = Literal["frustrated", "sad", "happy", "focused", "tired", "anxious", "calm"]
NeedName = Literal["comfort", "focus", "energy", "relaxation", "companionship"]
InputSource = Literal["text", "faster_whisper"]
PlayerState = Literal["idle", "loading", "playing", "paused", "error"]
PetState = Literal["idle", "focus", "tired", "frustrated", "sad"]
PlayAction = Literal["play", "pause", "skip", "none"]
EndedReason = Literal["finished", "skipped", "stopped", "unknown"]


class ContextModel(BaseModel):
    hour: int = Field(ge=0, le=23)
    active_app: str = Field(min_length=1)
    kpm: int = Field(ge=0)
    backspace_ratio: float = Field(ge=0.0, le=1.0)


class TranscribeRequest(BaseModel):
    audio: str = Field(min_length=1)
    audio_format: str = "wav"


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1)
    input_source: InputSource
    context: ContextModel


class TranscribeResponse(BaseModel):
    transcript: str
    language: str = "zh"
    source: str = "faster-whisper"


class EmotionResult(BaseModel):
    emotion: EmotionName
    energy: float = Field(ge=0.0, le=1.0)
    need: NeedName


class SongResponse(BaseModel):
    id: str
    title: str
    artist: str
    tags: list[str]
    energy: float
    mood: str
    file_path: str
    description: str | None = None
    audio_features: dict = Field(default_factory=dict)
    semantic_features: dict = Field(default_factory=dict)
    play_count: int = 0
    avg_completion_rate: float = 0.0


class AnalyzeResponse(BaseModel):
    transcript: str
    emotion: EmotionResult
    current_state: PetState
    bubble_text: str
    assistant_reply: str
    recommendation: SongResponse
    play_action: PlayAction
    player_status: PlayerState
    session_id: str | None = None
    retrieval_query: str | None = None
    playlist: list[SongResponse] = Field(default_factory=list)


class MemoryEntry(BaseModel):
    timestamp: datetime
    context: ContextModel
    emotion: EmotionResult
    song_id: str


class MemoryResponse(BaseModel):
    entries: list[MemoryEntry]
    total: int


class PlayerStatusResponse(BaseModel):
    player: str = "mpv"
    status: PlayerState
    track_id: str | None = None
    title: str | None = None
    artist: str | None = None


class PlayerEventRequest(BaseModel):
    session_id: str = Field(min_length=1)
    event: str = "ended"
    completion_rate: float = Field(ge=0.0, le=1.0)
    ended_reason: EndedReason = "unknown"


class PlayerEventResponse(BaseModel):
    status: str = "ok"
    message: str = "Player event recorded"
