"""pytest 公共测试配置。"""

import json
import os
import tempfile
from collections.abc import Generator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ["OPENAI_API_KEY"] = ""
os.environ["ENABLE_MPV"] = "false"

from backend.main import app  # noqa: E402
from backend.models.database import Base, get_db  # noqa: E402
from backend.models.tables import Song  # noqa: E402
from backend.services.player_service import reset_for_tests  # noqa: E402
from backend.services.playlist_service import reset_for_tests as reset_playlist  # noqa: E402


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = create_engine(
            f"sqlite:///{tmp_dir}/test.db",
            connect_args={"check_same_thread": False},
        )
        TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        Base.metadata.create_all(bind=engine)
        db = TestingSessionLocal()
        _add_test_songs(db)

        try:
            yield db
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)
            engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    reset_for_tests()
    reset_playlist()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _add_test_songs(db: Session) -> None:
    songs = [
        Song(
            id="s001",
            title="Steady Low",
            artist="Test",
            file_path="C:/music/s001.mp3",
            tags="[]",
            energy=0.3,
            mood="neutral",
            description="中等偏低能量、节奏稳定、有支撑感、不吵的器乐音乐",
            audio_features=json.dumps({"bpm": 90}),
            semantic_features="{}",
            embedding=json.dumps([1.0, 0.0, 0.0]),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Song(
            id="s002",
            title="Bright Fast",
            artist="Test",
            file_path="C:/music/s002.mp3",
            tags="[]",
            energy=0.8,
            mood="neutral",
            description="快速、响度较高、频谱明亮、动态丰富的音乐",
            audio_features=json.dumps({"bpm": 150}),
            semantic_features="{}",
            embedding=json.dumps([0.0, 1.0, 0.0]),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]
    db.add_all(songs)
    db.commit()
