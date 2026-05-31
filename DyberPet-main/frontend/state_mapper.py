"""Map backend payloads to the simplified EchoPet frontend view model."""

from __future__ import annotations

from typing import Dict, Iterable


DEFAULT_BUBBLES = {
    "idle": "我在这里陪着你。",
    "focus": "先帮你稳住节奏，慢慢进入心流。",
    "focused_stressed": "先帮你把高强度输出稳住。",
    "tired": "你看起来有点累，我放轻一点的。",
    "frustrated": "先别急，我帮你把状态缓下来。",
    "sad": "没关系，我先陪你待一会儿。",
}

STATE_ACTION_CANDIDATES = {
    "idle": ["站立", "default", "stand"],
    # EchoDeer currently ships a smaller action set than the original DyberPet
    # defaults, so keep visible fallbacks here for API mode and debug mode.
    "focus": ["focus", "lazy", "站立", "default", "stand"],
    "tired": ["lazy", "sad", "站立", "default", "stand"],
    "frustrated": ["anxious", "sad", "onfloor", "lazy", "站立", "default", "stand"],
    "sad": ["sad", "onfloor", "lazy", "站立", "default", "stand"],
}

EMOTION_TO_STATE = {
    "focused": "focus",
    "tired": "tired",
    "frustrated": "frustrated",
    "sad": "sad",
    "anxious": "frustrated",
    "happy": "idle",
    "calm": "idle",
}


def normalize_state(raw_state: str | None, emotion: str | None = None) -> str:
    if raw_state in DEFAULT_BUBBLES:
        return raw_state
    if emotion in EMOTION_TO_STATE:
        return EMOTION_TO_STATE[emotion]
    return "idle"


def pick_action_for_state(state_name: str, available_actions: Iterable[str]) -> str | None:
    available = set(available_actions)
    for action_name in STATE_ACTION_CANDIDATES.get(state_name, []):
        if action_name in available:
            return action_name
    return None


def normalize_player_status(payload: Dict | None) -> Dict:
    payload = payload or {}
    return {
        "player": payload.get("player", "mpv"),
        "status": payload.get("status", "idle"),
        "track_id": payload.get("track_id", ""),
        "title": payload.get("title", ""),
        "artist": payload.get("artist", ""),
    }


def map_agent_result(result: Dict | None) -> Dict:
    result = result or {}
    emotion_payload = result.get("emotion") or {}
    emotion_name = emotion_payload.get("emotion")
    pet_state = normalize_state(result.get("current_state"), emotion_name)

    recommendation = result.get("recommendation") or {}
    player_status = normalize_player_status(
        {
            "player": "mpv",
            "status": result.get("player_status", "idle"),
            "track_id": recommendation.get("id", ""),
            "title": recommendation.get("title", ""),
            "artist": recommendation.get("artist", ""),
        }
    )

    bubble_text = (
        result.get("bubble_text")
        or result.get("assistant_reply")
        or DEFAULT_BUBBLES[pet_state]
    )
    assistant_reply = result.get("assistant_reply") or bubble_text

    return {
        "pet_state": pet_state,
        "bubble_text": bubble_text,
        "assistant_reply": assistant_reply,
        "recommendation": recommendation,
        "session_id": result.get("session_id") or "",
        "retrieval_query": result.get("retrieval_query") or "",
        "playlist": result.get("playlist") or [],
        "player_status": player_status,
        "play_action": result.get("play_action", "none"),
        "transcript": result.get("transcript", ""),
        "debug_mode": result.get("_mode", "api"),
        "debug_error": result.get("_error", ""),
    }
