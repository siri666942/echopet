"""Global EchoPet hotkeys."""

from __future__ import annotations

import threading
from typing import Callable

from pynput import keyboard


NUMPAD_ACTIONS = {
    97: "pause",
    98: "skip",
    99: "voice",
}


class EchoPetHotkeyListener:
    """Listen for Ctrl+Alt+Numpad 1/2/3."""

    def __init__(
        self,
        on_pause: Callable[[], None],
        on_skip: Callable[[], None],
        on_voice: Callable[[], None],
    ):
        self._callbacks = {
            "pause": on_pause,
            "skip": on_skip,
            "voice": on_voice,
        }
        self._pressed_modifiers: set[str] = set()
        self._active_actions: set[str] = set()
        self._lock = threading.Lock()
        self._listener: keyboard.Listener | None = None

    def start(self) -> None:
        if self._listener is not None:
            return
        listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
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

    def _on_press(self, key) -> None:
        action_to_fire = None
        with self._lock:
            modifier = self._modifier_name(key)
            if modifier:
                self._pressed_modifiers.add(modifier)
                return

            action = NUMPAD_ACTIONS.get(getattr(key, "vk", None))
            if action and {"ctrl", "alt"}.issubset(self._pressed_modifiers):
                if action not in self._active_actions:
                    self._active_actions.add(action)
                    action_to_fire = action

        if action_to_fire:
            self._callbacks[action_to_fire]()

    def _on_release(self, key) -> None:
        with self._lock:
            modifier = self._modifier_name(key)
            if modifier:
                self._pressed_modifiers.discard(modifier)
                self._active_actions.clear()
                return

            action = NUMPAD_ACTIONS.get(getattr(key, "vk", None))
            if action:
                self._active_actions.discard(action)

    def _modifier_name(self, key) -> str | None:
        if key in {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}:
            return "ctrl"
        if key in {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr}:
            return "alt"
        return None
