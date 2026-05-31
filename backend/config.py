"""后端配置文件。

这个文件解决一个问题：

    "代码里需要很多配置，比如数据库在哪、音乐目录在哪、OpenAI Key 是什么。
     这些值不要散落在各个文件里，要集中管理。"

配置来源有两种：

1. 默认值
   - 比如数据库默认放到 `backend/db/echopet.db`。

2. 项目根目录的 `.env`
   - 如果你写了 `.env`，里面的值会覆盖默认值。
   - 例如 `.env` 里写 `OPENAI_API_KEY=xxx`，代码就能读到。

注意：
    `.env` 不要提交 git，因为里面可能有 API Key。
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# `BACKEND_DIR` 是 backend 目录的绝对路径。
# 后面拼数据库路径、音乐路径，都基于它来算，避免"从不同目录启动命令时路径错乱"。
BACKEND_DIR = Path(__file__).resolve().parent
ESSENTIA_MODEL_DIR = BACKEND_DIR / "models" / "essentia"


class Settings(BaseSettings):
    """全项目统一配置对象。

    字段名会自动映射环境变量。
    例如：
        `openai_api_key` 会读取 `.env` 里的 `OPENAI_API_KEY`。

    你可以把它理解成一个"配置表"。
    业务代码不要自己到处读 `.env`，统一从 `settings` 取。
    """

    # 服务基础信息，主要用于 Swagger 和启动命令。
    app_name: str = "EchoPet API"
    app_version: str = "0.2.0"
    host: str = "127.0.0.1"
    port: int = 8000

    # SQLite 默认数据库路径。
    # 最终会变成类似：sqlite:///C:/.../echopet/backend/db/echopet.db
    database_url: str = f"sqlite:///{(BACKEND_DIR / 'db' / 'echopet.db').as_posix()}"

    # 本地曲库目录。
    # 用户可以把 mp3/wav/flac 放到这里，启动时会扫描入库。
    music_dir: Path = BACKEND_DIR / "music"

    # OpenAI 兼容 API 配置。
    # 如果没有 key，emotion_service 会自动使用关键词规则兜底。
    # base_url 用于接入 OpenAI 兼容的第三方服务（如 StepFun、DeepSeek 等）。
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_provider: str = "local"
    local_embedding_model: str = "BAAI/bge-small-zh-v1.5"
    local_embedding_cache_dir: Path = BACKEND_DIR / "models" / "fastembed"

    # Essentia TensorFlow 模型目录。
    # Docker 里这个目录会映射到宿主机 `backend/models/essentia/`。
    # 模型文件很大，不提交 git，但下载一次后会保留在本地。
    essentia_model_dir: Path = ESSENTIA_MODEL_DIR

    # Essentia TensorFlow 模型路径。
    # 这些默认值对应 `backend/scripts/download_essentia_models.py` 下载的官方模型文件。
    # 如果模型文件不存在，新歌会入库失败；系统不会生成假特征。
    essentia_msd_embedding_model_path: str = str(ESSENTIA_MODEL_DIR / "msd-musicnn-1.pb")
    essentia_discogs_embedding_model_path: str = str(ESSENTIA_MODEL_DIR / "discogs-effnet-bs64-1.pb")
    essentia_genre_model_path: str = str(ESSENTIA_MODEL_DIR / "genre_discogs400-discogs-effnet-1.pb")
    essentia_mood_model_path: str = str(ESSENTIA_MODEL_DIR / "moods_mirex-msd-musicnn-1.pb")
    essentia_danceability_model_path: str = str(ESSENTIA_MODEL_DIR / "danceability-msd-musicnn-1.pb")
    essentia_arousal_valence_model_path: str = str(ESSENTIA_MODEL_DIR / "deam-msd-musicnn-2.pb")
    essentia_voice_instrumental_model_path: str = str(ESSENTIA_MODEL_DIR / "voice_instrumental-msd-musicnn-1.pb")
    essentia_acoustic_electronic_model_path: str = str(ESSENTIA_MODEL_DIR / "nsynth_acoustic_electronic-discogs-effnet-1.pb")

    # faster-whisper 配置。
    # 模型不可用时，whisper_service 会返回 503，避免前端把空转写当成功。
    whisper_model: str = "base"
    whisper_model_dir: Path = BACKEND_DIR / "models" / "faster-whisper"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    # mpv 配置。
    # `enable_mpv=false` 时，后端不会尝试真实播放，只维护状态。
    mpv_binary: str = "mpv"
    enable_mpv: bool = True

    # 告诉 pydantic-settings：去项目根目录读取 `.env`。
    # extra="ignore" 表示 `.env` 里有暂时用不到的字段也不要报错。
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """创建并缓存 Settings。

    为什么要缓存：
        配置对象创建一次就够了。
        `@lru_cache` 会让后续调用直接复用同一个对象。

    这里还顺手创建运行时目录：
        - 音乐目录
        - 数据库目录

    这样第一次启动时，即使目录不存在，服务也能自己准备好。
    """

    settings = Settings()

    # 确保 `backend/music/` 存在。
    settings.music_dir.mkdir(parents=True, exist_ok=True)
    settings.essentia_model_dir.mkdir(parents=True, exist_ok=True)
    settings.local_embedding_cache_dir.mkdir(parents=True, exist_ok=True)
    settings.whisper_model_dir.mkdir(parents=True, exist_ok=True)

    # 如果用的是 SQLite，就解析出 db 文件路径，确保父目录存在。
    db_path = _sqlite_path(settings.database_url)
    if db_path is not None:
        db_path.parent.mkdir(parents=True, exist_ok=True)

    return settings


def _sqlite_path(database_url: str) -> Path | None:
    """从 SQLite URL 中取出真实文件路径。

    参数：
        database_url:
            形如 `sqlite:///backend/db/echopet.db` 的数据库连接字符串。

    返回：
        - 如果是 SQLite，返回数据库文件路径。
        - 如果不是 SQLite，返回 None。

    这个函数目前只服务于"自动创建数据库目录"。
    """

    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return None
    return Path(database_url[len(prefix) :])


# 全项目直接 import 这个 `settings` 使用。
# 例如：`from backend.config import settings`
settings = get_settings()
