"""进程内播放队列。"""

from backend.models.tables import Song


_playlist: list[Song] = []
_cursor = 0


def set_playlist(songs: list[Song]) -> None:
    global _playlist, _cursor
    _playlist = list(songs)
    _cursor = 0


def get_current_playlist() -> list[Song]:
    return list(_playlist)


def get_next_song() -> Song | None:
    global _cursor
    _cursor += 1
    if _cursor >= len(_playlist):
        return None
    return _playlist[_cursor]


def reset_for_tests() -> None:
    global _playlist, _cursor
    _playlist = []
    _cursor = 0
