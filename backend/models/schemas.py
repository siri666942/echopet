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
PetState = Literal["idle", "focus", "tired", "frustrated", "sad", "focused_stressed"]
PlayAction = Literal["play", "pause", "skip", "none"]
EndedReason = Literal["finished", "skipped", "stopped", "unknown"]


class ContextModel(BaseModel):
    hour: int = Field(ge=0, le=23)
    active_app: str = Field(min_length=1)
    kpm: int = Field(ge=0)
    backspace_ratio: float = Field(ge=0.0, le=1.0)


class KeyboardEvent(BaseModel):
    key: str = Field(min_length=1)
    type: Literal["keydown", "keyup"]
    timestamp: float


class KeyboardEventWindow(BaseModel):
    window_seconds: int = Field(default=60, gt=0, le=600)
    events: list[KeyboardEvent] = Field(default_factory=list)
    active_app: str | None = None


class KeyboardFeatures(BaseModel):
    window_seconds: int | float = 60
    key_count: int = Field(ge=0)
    kpm: int = Field(ge=0)
    backspace_count: int = Field(ge=0)
    backspace_ratio: float = Field(ge=0.0, le=1.0)
    pause_count: int = Field(ge=0)
    long_pause_count: int = Field(ge=0)
    max_pause: float = Field(ge=0.0)
    dwell_mean: float = Field(ge=0.0)
    dwell_std: float = Field(ge=0.0)
    flight_mean: float = Field(ge=0.0)
    flight_std: float = Field(ge=0.0)
    dd_interval_mean: float = Field(ge=0.0)
    dd_interval_std: float = Field(ge=0.0)
    burst_count: int = Field(ge=0)
    typing_stability: float = Field(ge=0.0, le=1.0)


class KeyboardState(BaseModel):
    focus: float = Field(ge=0.0, le=1.0)
    stress: float = Field(ge=0.0, le=1.0)
    fatigue: float = Field(ge=0.0, le=1.0)
    stability: float = Field(ge=0.0, le=1.0)
    typing_state: str = Field(min_length=1)


class TranscribeRequest(BaseModel):
    audio: str = Field(min_length=1)
    audio_format: str = "wav"


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1)
    input_source: InputSource
    context: ContextModel
    keyboard_events: KeyboardEventWindow | None = None
    keyboard_state: KeyboardState | None = None


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
