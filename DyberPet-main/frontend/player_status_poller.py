"""Polling wrapper for mpv status."""

from __future__ import annotations

import threading

from PySide6.QtCore import QObject, QTimer, Signal


class PlayerStatusPoller(QObject):
    status_updated = Signal(dict)
    poll_failed = Signal(str)

    def __init__(self, agent_client, interval_ms: int = 5000, parent=None):
        super().__init__(parent)
        self.agent_client = agent_client
        self.timer = QTimer(self)
        self.timer.setInterval(interval_ms)
        self.timer.timeout.connect(self.refresh_now)
        self._request_lock = threading.Lock()
        self._running = False

    def start(self) -> None:
        if not self.timer.isActive():
            self.timer.start()
        self.refresh_now()

    def stop(self) -> None:
        self.timer.stop()

    def refresh_now(self) -> None:
        with self._request_lock:
            if self._running:
                return
            self._running = True
        threading.Thread(target=self._poll_in_background, daemon=True).start()

    def _poll_in_background(self) -> None:
        try:
            status_payload = self.agent_client.get_player_status(timeout=0.6)
            self.status_updated.emit(status_payload)
        except Exception as exc:  # pragma: no cover - defensive UI wrapper
            self.poll_failed.emit(str(exc))
        finally:
            with self._request_lock:
                self._running = False
