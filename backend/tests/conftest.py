"""pytest 公共测试配置。

这个文件不是业务代码，但它决定所有测试怎么跑。

核心目标：
    每个测试都使用一个干净的临时 SQLite 数据库，
    不污染你真实运行时的 `backend/db/echopet.db`。
"""

import os
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# 测试时强制关闭外部依赖。
# 这样测试不会真的调用 OpenAI，也不会真的启动 mpv。
os.environ["OPENAI_API_KEY"] = ""
os.environ["ENABLE_MPV"] = "false"

# noqa: E402 的意思是忽略“import 必须放文件顶部”的 lint 提示。
# 因为这里必须先设置环境变量，再 import app/config。
from backend.main import app  # noqa: E402
from backend.models.database import Base, get_db  # noqa: E402
from backend.services.music_service import add_sample_songs  # noqa: E402
from backend.services.player_service import reset_for_tests  # noqa: E402


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """给每个测试创建独立数据库。

    流程：
        1. 创建临时目录。
        2. 在临时目录里创建 test.db。
        3. 根据 SQLAlchemy 表模型建表。
        4. 插入样例歌曲。
        5. 把 db session 交给测试用。
        6. 测试结束后关闭连接、删表、释放 engine。
    """

    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = create_engine(
            f"sqlite:///{tmp_dir}/test.db",
            connect_args={"check_same_thread": False},
        )
        TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

        Base.metadata.create_all(bind=engine)
        db = TestingSessionLocal()
        add_sample_songs(db)

        try:
            yield db
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)

            # Windows 会锁 SQLite 文件。
            # dispose 可以主动释放连接池，否则临时目录删除可能失败。
            engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """创建 FastAPI 测试客户端。

    关键点：
        正常运行时，API 通过 get_db() 连接真实数据库。
        测试时，我们用 app.dependency_overrides 把 get_db 替换成临时数据库。

    这样每个测试都不会碰真实数据。
    """

    reset_for_tests()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
