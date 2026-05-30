"""Thin adapter for the backend /api/transcribe endpoint."""

from __future__ import annotations

import base64

from frontend.agent_client import AgentClient, AgentClientError


class WhisperAdapter:
    def __init__(self, agent_client: AgentClient):
        self.agent_client = agent_client

    def transcribe_audio_bytes(self, audio_bytes: bytes, audio_format: str = "wav") -> dict:
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        try:
            return self.agent_client.transcribe_audio(audio_b64, audio_format=audio_format)
        except AgentClientError as exc:
            raise RuntimeError(f"转写服务不可用: {exc}") from exc
