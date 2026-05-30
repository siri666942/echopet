"""数据库连接和 Session 管理。

先把几个概念讲清楚：

1. engine
   - 可以理解成“数据库发动机”。
   - 它知道数据库在哪里、怎么连接。

2. Session
   - 可以理解成“一次数据库操作窗口”。
   - 查数据、插数据、提交事务，都通过 Session 做。

3. Base
   - 所有 SQLAlchemy 表模型的父类。
   - `Song(Base)`、`Memory(Base)` 这些表都继承它。
   - `Base.metadata.create_all()` 会根据这些表模型创建真实数据库表。

4. get_db
   - FastAPI 的依赖函数。
   - API 函数里写 `db: Session = Depends(get_db)`，FastAPI 就会自动打开/关闭数据库连接。
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import settings


# 创建数据库 engine。
# 如果是 SQLite，需要加 `check_same_thread=False`。
# 原因：
#   FastAPI 处理请求时可能跨线程使用连接；
#   SQLite 默认不允许一个连接跨线程使用；
#   这个参数是常见的 FastAPI + SQLite 配置。
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)

# SessionLocal 是“Session 工厂”。
# 你调用 `SessionLocal()`，就会得到一个新的数据库会话。
#
# autoflush=False:
#   不要在每次查询前自动 flush，行为更可控。
#
# autocommit=False:
#   不要自动提交，明确调用 db.commit() 才保存。
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """所有数据库表模型的父类。"""


def init_db() -> None:
    """创建数据库表。

    这句 `from backend.models import tables` 看起来像没用，其实很重要。

    原因：
        SQLAlchemy 只有在 Python 加载了 Song/Memory 类之后，
        才知道有哪些表需要创建。

    所以这里显式 import tables，确保表模型已经注册到 Base.metadata。
    """

    from backend.models import tables  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """给 FastAPI 路由使用的数据库依赖。

    使用方式：
        async def api(db: Session = Depends(get_db)):
            ...

    执行过程：
        1. 请求进来时，创建 db = SessionLocal()
        2. 把 db 交给接口函数用
        3. 接口结束后，无论成功失败，都 db.close()
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
