"""EchoPet 后端总入口。

你可以把这个文件理解成“后端服务的总开关”。

它做 4 件事：

1. 创建 FastAPI 应用对象 `app`
   - `uvicorn backend.main:app ...` 启动时，找的就是这里的 `app`。

2. 在服务启动时准备运行环境
   - 建 SQLite 表。
   - 扫描本地曲库。
   - 如果曲库为空，插入几条样例歌曲，保证前端演示不会因为“没歌”直接断掉。

3. 配置 CORS
   - 前端 DyberPet 和后端不是同一个进程。
   - 前端请求后端时，浏览器/桌面 WebView 可能会检查跨域。
   - 这里先全部放开，方便黑客松/MVP 联调。

4. 挂载所有 API 路由
   - `backend/api/*.py` 每个文件管一类接口。
   - 这里统一把它们接到 FastAPI 应用上。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 这些 import 是“路由模块”。
# 举例：`analyze.router` 里面定义了 `POST /api/analyze`。
# main.py 自己不写具体业务逻辑，只负责把各个路由模块装配起来。
from backend.api import analyze, context, feedback, memory, music, player, transcribe
from backend.config import settings
from backend.models.database import SessionLocal, init_db
from backend.services.music_service import initialize_library


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 生命周期钩子。

    这个函数会在服务启动时先执行 `yield` 之前的代码；
    服务关闭时再执行 `yield` 之后的代码。

    这里暂时只需要启动初始化：

    - `init_db()`：创建数据库表。
    - `SessionLocal()`：打开一个数据库连接。
    - `initialize_library(db)`：扫描曲库并插入样例歌曲。

    参数：
        app:
            FastAPI 应用对象。这个参数是 FastAPI 生命周期函数固定会传进来的。
            当前代码里暂时不需要用它，但函数签名必须接收它。
    """

    # 第一步：确保数据库表存在。
    # 如果表已经存在，SQLAlchemy 不会重复创建。
    init_db()

    # 第二步：打开一个临时数据库会话，用来做启动时的曲库初始化。
    db = SessionLocal()
    try:
        # 扫描 `backend/music/`，把音乐文件登记到 songs 表。
        # 如果目录里没有音乐，就插入 3 条假数据，方便前端先跑通流程。
        initialize_library(db)
    finally:
        # 数据库连接用完必须关掉。
        # 不关的话，在 Windows 上尤其容易出现文件被占用的问题。
        db.close()

    # 到这里为止，服务启动准备完成，FastAPI 开始真正对外提供接口。
    yield


# 创建 FastAPI 应用。
# title/version 会显示在 Swagger 页面： http://127.0.0.1:8000/docs
app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

# CORS 配置。
# MVP 阶段为了让前端随便联调，全部放开。
# 如果将来上线，应该把 allow_origins 改成具体前端地址。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 把各个路由模块接到主 app 上。
# 这些 router 自己已经带了 prefix="/api"。
app.include_router(transcribe.router)  # POST /api/transcribe
app.include_router(analyze.router)  # POST /api/analyze
app.include_router(feedback.router)  # POST /api/feedback
app.include_router(context.router)  # GET /api/context
app.include_router(memory.router)  # GET /api/memory
app.include_router(player.router)  # GET /api/player/status
app.include_router(music.router)  # GET /api/music/random


@app.get("/")
def root() -> dict:
    """服务健康检查。

    打开 `http://127.0.0.1:8000/` 时会走到这里。
    它不做业务，只告诉你：后端活着，版本是多少。
    """

    return {"service": "EchoPet API", "version": settings.app_version}
