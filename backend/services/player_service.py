"""播放器服务。

这个文件负责和 mpv 播放器交互。

核心原则：
    播放失败不能拖垮 `/api/analyze`。

原因：
    本地机器可能没装 mpv；
    样例歌曲路径可能不存在；
    python-mpv 依赖可能不可用。

所以这里所有播放异常都会被吃掉，然后把状态设成 error。
前端可以看到 error，但后端接口不会 500 崩掉。
"""

from __future__ import annotations

from backend.config import settings
from backend.services import playlist_service


# mpv 播放器实例。
# 一开始是 None，第一次需要播放时才创建。
_player = None

# 当前播放器状态。
_status = "idle"

# 当前歌曲信息。
# 即使 mpv 播放失败，我们也保留这份信息，方便前端展示"刚才尝试播放哪首"。
_current_track: dict[str, str] | None = None


def play(file_path: str, track_id: str, title: str, artist: str) -> str:
    """播放一首歌。

    参数：
        file_path:
            本地音频文件路径，mpv 靠它找文件。

        track_id:
            歌曲 ID，比如 s001。

        title:
            歌名。

        artist:
            艺术家。

    返回：
        当前播放器状态字符串。
    """

    global _current_track, _status

    _current_track = {"track_id": track_id, "title": title, "artist": artist}
    _status = "loading"

    # 如果 .env 里 ENABLE_MPV=false，就完全不尝试真实播放。
    # 这对没有 mpv 的开发环境很友好。
    if not settings.enable_mpv:
        _status = "idle"
        return _status

    try:
        player = _get_player()
        if player is None:
            _status = "error"
            return _status

        # 真正调用 mpv 播放。
        player.play(file_path)
    except Exception:
        # 不把异常抛到 API 层。
        # 播放失败只是播放器状态问题，不应该让推荐接口失败。
        _status = "error"

    return _status


def toggle_pause() -> str:
    """Toggle playback pause state."""

    global _status

    if _status == "playing":
        if settings.enable_mpv:
            try:
                player = _get_player()
                if player is not None:
                    player.pause = True
            except Exception:
                _status = "error"
                return _status
        _status = "paused"
        return _status

    if _status == "paused":
        if settings.enable_mpv:
            try:
                player = _get_player()
                if player is not None:
                    player.pause = False
            except Exception:
                _status = "error"
                return _status
        _status = "playing"
        return _status

    return _status


def skip_to_next() -> dict:
    """切到播放队列中的下一首。"""

    next_song = playlist_service.get_next_song()
    if next_song is None:
        _clear_track()
        _stop_player()
        return get_status()

    play(next_song.file_path, next_song.id, next_song.title, next_song.artist)
    return get_status()


def get_status() -> dict:
    """返回当前播放器状态。

    `/api/player/status` 会直接调用它。
    """

    _refresh_status_from_player()

    return {
        "player": "mpv",
        "status": _status,
        "track_id": _current_track["track_id"] if _current_track else None,
        "title": _current_track["title"] if _current_track else None,
        "artist": _current_track["artist"] if _current_track else None,
    }


def reset_for_tests() -> None:
    """测试用：重置播放器内存状态。"""

    global _current_track, _status, _player
    _current_track = None
    _status = "idle"
    _player = None


def _get_player():
    """懒加载 mpv 播放器实例。

    "懒加载"的意思是：
        服务启动时不马上创建 mpv；
        第一次真正播放时才创建。

    好处：
        没装 mpv 时，服务仍然能启动。
    """

    global _player
    if _player is not None:
        return _player

    try:
        import mpv

        _player = mpv.MPV(
            input_default_bindings=True,
            input_vo_keyboard=True,
            idle=True,
            ytdl=False,
        )
    except Exception:
        _player = None

    return _player


def _refresh_status_from_player() -> None:
    global _status

    if not settings.enable_mpv or _status == "error":
        return

    player = _get_player()
    if player is None:
        return

    try:
        is_paused = bool(getattr(player, "pause", False))
        is_idle = bool(
            getattr(player, "idle_active", False) or getattr(player, "core_idle", False)
        )
    except Exception:
        _status = "error"
        return

    if is_paused and _current_track:
        _status = "paused"
        return

    if is_idle:
        if _current_track and _status in {"loading", "playing", "paused"}:
            if playlist_service.has_next_song():
                skip_to_next()
            else:
                _clear_track()
                _status = "idle"
        elif _status != "error":
            _status = "idle"
        return

    if _current_track and _status in {"loading", "idle", "paused"}:
        _status = "playing"


def _clear_track() -> None:
    global _current_track
    _current_track = None


def _stop_player() -> None:
    global _status

    if settings.enable_mpv:
        try:
            player = _get_player()
            if player is not None:
                player.stop()
        except Exception:
            _status = "error"
            return
    _status = "idle"
