"""测试播放队列。"""

from backend.services import playlist_service
from backend.models.tables import Song


def test_playlist_next_song(db_session):
    songs = db_session.query(Song).order_by(Song.id).all()
    playlist_service.set_playlist(songs)

    assert len(playlist_service.get_current_playlist()) == 2
    assert playlist_service.get_next_song().id == "s002"
    assert playlist_service.get_next_song() is None
