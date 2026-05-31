"""Privacy-preserving keyboard rhythm tracker for EchoPet."""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Deque, Dict

from pynput import keyboard


class KeyboardTracker:
    def __init__(self, retention_seconds: int = 60):
        self.retention_seconds = retention_seconds
        self._events: Deque[Dict] = deque()
        self._lock = threading.Lock()
        self._listener: keyboard.Listener | None = None

    def start(self) -> None:
        if self._listener is not None:
            return
        listener = keyboard.Listener(
            on_press=lambda key: self._record(key, "keydown"),
            on_release=lambda key: self._record(key, "keyup"),
        )
        listener.daemon = True
        try:
            listener.start()
        except Exception:
            self._listener = None
            return
        self._listener = listener

    def stop(self) -> None:
        listener = self._listener
        self._listener = None
        if listener is not None:
            listener.stop()

    def snapshot(self, window_seconds: int = 60) -> Dict:
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            self._trim_locked(now)
            events = [event.copy() for event in self._events if event["timestamp"] >= cutoff]
        return {
            "window_seconds": window_seconds,
            "events": events,
        }

    def _record(self, key, event_type: str) -> None:
        now = time.time()
        event = {
            "key": self._normalize_key(key),
            "type": event_type,
            "timestamp": now,
        }
        with self._lock:
            self._events.append(event)
            self._trim_locked(now)

    def _trim_locked(self, now: float) -> None:
        cutoff = now - self.retention_seconds
        while self._events and self._events[0]["timestamp"] < cutoff:
            self._events.popleft()

    def _normalize_key(self, key) -> str:
        char = getattr(key, "char", None)
        if char:
            return "CHAR"

        name = getattr(key, "name", None)
        if name:
            return self._normalize_special_name(name)

        raw = str(key).replace("Key.", "")
        if len(raw) == 3 and raw.startswith("'") and raw.endswith("'"):
            return "CHAR"
        return self._normalize_special_name(raw)

    def _normalize_special_name(self, name: str) -> str:
        normalized = name.strip().lower()
        mapping = {
            "space": "Space",
            "enter": "Enter",
            "return": "Enter",
            "backspace": "Backspace",
            "tab": "Tab",
            "esc": "Esc",
            "escape": "Esc",
            "delete": "Delete",
            "del": "Delete",
            "shift": "Shift",
            "shift_l": "Shift",
            "shift_r": "Shift",
            "ctrl": "Ctrl",
            "ctrl_l": "Ctrl",
            "ctrl_r": "Ctrl",
            "alt": "Alt",
            "alt_l": "Alt",
            "alt_r": "Alt",
            "cmd": "Meta",
            "cmd_l": "Meta",
            "cmd_r": "Meta",
            "left": "ArrowLeft",
            "right": "ArrowRight",
            "up": "ArrowUp",
            "down": "ArrowDown",
        }
        return mapping.get(normalized, normalized.title() or "Unknown")
