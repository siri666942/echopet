"""Local audio playback for the Windows desktop frontend."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class LocalAudioPlayer(QObject):
    status_changed = Signal(dict)

    def __init__(self, repo_root: Path, parent=None):
        super().__init__(parent)
        self.repo_root = repo_root
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0.65)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio_output)
        self.playlist: List[Dict] = []
        self.index = -1
        self.current_track: Dict = {}
        self.status = "idle"

        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.errorOccurred.connect(self._on_error)

    def set_playlist(self, playlist: List[Dict], start_index: int = 0) -> None:
        self.playlist = list(playlist or [])
        self.index = start_index if self.playlist else -1

    def play_track(self, track: Dict) -> Dict:
        path = self._resolve_file_path(track.get("file_path", ""))
        self.current_track = dict(track or {})
        if not path or not path.exists():
            self.status = "error"
            self._emit_status()
            return self.get_status()

        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.player.play()
        self.status = "playing"
        self._emit_status()
        return self.get_status()

    def play_current_or_resume(self) -> Dict:
        if self.status == "paused":
            self.player.play()
            self.status = "playing"
            self._emit_status()
            return self.get_status()
        if self.status in {"idle", "error"} and self.current_track:
            return self.play_track(self.current_track)
        if self.status == "playing":
            self.player.pause()
            self.status = "paused"
            self._emit_status()
        return self.get_status()

    def skip(self) -> Dict:
        if self.playlist and self.index + 1 < len(self.playlist):
            self.index += 1
            return self.play_track(self.playlist[self.index])
        self.status = "idle"
        self.player.stop()
        self._emit_status()
        return self.get_status()

    def get_status(self) -> Dict:
        return {
            "player": "qt-local",
            "status": self.status,
            "track_id": self.current_track.get("id", ""),
            "title": self.current_track.get("title", ""),
            "artist": self.current_track.get("artist", ""),
        }

    def _resolve_file_path(self, raw_path: str) -> Path | None:
        if not raw_path:
            return None

        path_text = raw_path.replace("\\", "/")
        if path_text.startswith("/app/backend/music/"):
            relative = path_text.removeprefix("/app/backend/music/")
            return self.repo_root / "backend" / "music" / relative

        path = Path(raw_path)
        if path.is_absolute():
            return path
        return self.repo_root / path

    def _on_playback_state_changed(self, state) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.status = "playing"
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.status = "paused"
        elif state == QMediaPlayer.PlaybackState.StoppedState and self.status != "error":
            self.status = "idle"
        self._emit_status()

    def _on_error(self, _error, _message: str = "") -> None:
        self.status = "error"
        self._emit_status()

    def _emit_status(self) -> None:
        self.status_changed.emit(self.get_status())
