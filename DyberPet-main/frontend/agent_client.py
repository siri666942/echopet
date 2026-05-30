"""Minimal API client for EchoPet hackathon integration."""

from __future__ import annotations

import json
from typing import Dict, Optional
from urllib import error, request


class AgentClientError(RuntimeError):
    """Raised when the EchoPet backend is unavailable."""


class AgentClient:
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.last_result: Dict = {}
        self.last_player_status: Dict = {
            "player": "mpv",
            "status": "idle",
            "track_id": "",
            "title": "",
            "artist": "",
        }

    def _request_json(
        self,
        method: str,
        path: str,
        payload: Optional[Dict] = None,
        timeout: Optional[float] = None,
    ) -> Dict:
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, headers=headers, method=method.upper())
        request_timeout = self.timeout if timeout is None else timeout
        try:
            with request.urlopen(req, timeout=request_timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except (error.URLError, error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            raise AgentClientError(str(exc)) from exc

    def get_context(self, timeout: Optional[float] = None) -> Dict:
        return self._request_json("GET", "/api/context", timeout=timeout)

    def analyze_text(
        self,
        text: str,
        input_source: str = "text",
        context: Optional[Dict] = None,
        timeout: Optional[float] = None,
    ) -> Dict:
        if context is None:
            context = self.get_context(timeout=timeout)
        payload = {
            "text": text,
            "input_source": input_source,
            "context": context,
        }
        return self._request_json("POST", "/api/analyze", payload, timeout=timeout)

    def submit_text(self, text: str, input_source: str = "text") -> Dict:
        try:
            context = self.get_context()
            result = self.analyze_text(text, input_source=input_source, context=context)
            result["_mode"] = "api"
            self._cache_result(result)
            return result
        except AgentClientError as exc:
            mock_result = self.build_mock_result(text=text)
            mock_result["_mode"] = "mock"
            mock_result["_error"] = str(exc)
            self._cache_result(mock_result)
            return mock_result

    def get_player_status(self, timeout: Optional[float] = None) -> Dict:
        try:
            payload = self._request_json("GET", "/api/player/status", timeout=timeout)
            self.last_player_status = {
                "player": payload.get("player", "mpv"),
                "status": payload.get("status", "idle"),
                "track_id": payload.get("track_id", ""),
                "title": payload.get("title", ""),
                "artist": payload.get("artist", ""),
            }
        except AgentClientError:
            pass
        return self.last_player_status.copy()

    def send_player_event(
        self,
        session_id: str,
        completion_rate: float,
        ended_reason: str,
        event: str = "ended",
    ) -> Dict:
        if not session_id:
            return {"status": "ignored", "message": "当前没有可上报的播放会话"}
        try:
            return self._request_json(
                "POST",
                "/api/player/event",
                {
                    "session_id": session_id,
                    "event": event,
                    "completion_rate": completion_rate,
                    "ended_reason": ended_reason,
                },
            )
        except AgentClientError:
            return {"status": "ok", "message": "播放事件已在本地忽略，后端暂不可用"}

    def transcribe_audio(self, audio_b64: str, audio_format: str = "wav") -> Dict:
        return self._request_json(
            "POST",
            "/api/transcribe",
            {"audio": audio_b64, "audio_format": audio_format},
        )

    def build_mock_result(self, text: str = "", forced_state: Optional[str] = None) -> Dict:
        state = forced_state or self._guess_state_from_text(text)
        templates = {
            "idle": {
                "bubble": "我先陪着你，想听歌时和我说一声。",
                "reply": "我在这儿，你想要我什么时候开始推荐都可以。",
                "song": ("mock-idle", "Quiet Desk", "EchoPet Demo"),
                "need": "companionship",
                "emotion": "calm",
            },
            "focus": {
                "bubble": "进入专注模式，我给你铺一层不打扰的节奏。",
                "reply": "我感觉你现在适合专注一点，我先给你一首稳节奏的。",
                "song": ("mock-focus", "Focus Loop", "EchoPet Demo"),
                "need": "focus",
                "emotion": "focused",
            },
            "tired": {
                "bubble": "你有点累了，我放轻一点的。",
                "reply": "我感觉你有点疲惫，先放一首更柔和的缓一缓。",
                "song": ("mock-tired", "Late Night Reset", "EchoPet Demo"),
                "need": "relaxation",
                "emotion": "tired",
            },
            "frustrated": {
                "bubble": "先别急，我帮你把状态缓下来。",
                "reply": "你现在像是有点卡住了，我先放一首能稳住情绪的。",
                "song": ("mock-frustrated", "Debug Relief", "EchoPet Demo"),
                "need": "comfort",
                "emotion": "frustrated",
            },
            "sad": {
                "bubble": "我在，先陪你待一会儿。",
                "reply": "我先不打扰太多，放一首更温柔的陪着你。",
                "song": ("mock-sad", "Soft Company", "EchoPet Demo"),
                "need": "companionship",
                "emotion": "sad",
            },
        }
        template = templates[state]
        song_id, title, artist = template["song"]
        return {
            "transcript": text,
            "emotion": {
                "emotion": template["emotion"],
                "energy": 0.5,
                "need": template["need"],
            },
            "current_state": state,
            "bubble_text": template["bubble"],
            "assistant_reply": template["reply"],
            "recommendation": {
                "id": song_id,
                "title": title,
                "artist": artist,
                "tags": ["demo"],
                "energy": 0.5,
                "mood": template["need"],
                "file_path": "",
            },
            "play_action": "play" if state != "idle" else "none",
            "player_status": "playing" if state != "idle" else "idle",
            "session_id": "",
            "retrieval_query": "",
            "playlist": [],
        }

    def _cache_result(self, result: Dict) -> None:
        self.last_result = result.copy()
        recommendation = result.get("recommendation") or {}
        self.last_player_status = {
            "player": "mpv",
            "status": result.get("player_status", "idle"),
            "track_id": recommendation.get("id", ""),
            "title": recommendation.get("title", ""),
            "artist": recommendation.get("artist", ""),
        }

    def _guess_state_from_text(self, text: str) -> str:
        lowered = text.lower()
        rules = [
            (("烦", "崩", "debug", "报错", "卡住", "焦虑"), "frustrated"),
            (("累", "困", "晚", "疲惫", "熬夜"), "tired"),
            (("难过", "伤心", "失落", "低落", "想哭"), "sad"),
            (("专注", "focus", "心流", "学习", "写代码"), "focus"),
        ]
        for keywords, state in rules:
            if any(keyword in lowered for keyword in keywords):
                return state
        return "idle"
