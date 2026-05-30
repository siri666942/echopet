# EchoPet 后端开发指南

> 本文档为后端开发者提供完整的开发指导，包括技术栈、文件结构、模块职责和实现方案。
>
> 对齐黑客松架构：`DyberPet` 前端 + `faster-whisper` + `mpv` 播放

---

## 目录

- [技术栈](#技术栈)
- [文件结构](#文件结构)
- [环境搭建](#环境搭建)
- [模块职责](#模块职责)
- [接口维护清单](#接口维护清单)
- [各模块实现方案](#各模块实现方案)
- [开发顺序建议](#开发顺序建议)

---

## 技术栈

| 类别 | 选型 | 说明 |
|------|------|------|
| 语言 | Python 3.11+ | — |
| Web 框架 | FastAPI | 异步、自动文档、类型安全 |
| 数据库 | SQLite | 轻量，单文件，MVP 阶段足够 |
| ORM | SQLAlchemy 2.0 | 配合 SQLite，后续可迁移 |
| 语音转文字 | faster-whisper | 本地部署，不依赖外部 API |
| 情绪分析 | OpenAI GPT / Claude | LLM 推理 |
| 音频处理 | pydub / ffmpeg | 音频格式转换 |
| 播放器 | mpv | 后端通过 IPC 控制播放 |
| 环境感知 | psutil + win32gui | 获取活跃窗口、系统信息 |
| 配置管理 | pydantic-settings | .env 环境变量管理 |
| 测试 | pytest + httpx | 单元测试 + 接口测试 |

### 关键依赖

```
fastapi
uvicorn[standard]
sqlalchemy>=2.0
pydantic>=2.0
pydantic-settings
faster-whisper   # 本地语音转文字
openai           # GPT 情绪分析
anthropic        # Claude（可选）
psutil
pydub
pytest
httpx
python-multipart # 文件上传支持
python-mpv       # mpv IPC 控制
```

---

## 文件结构

```
backend/
├── main.py                  # FastAPI 入口，挂载路由
├── config.py                # 配置项（API Key、路径、端口等）
├── requirements.txt         # Python 依赖
│
├── api/                     # 路由层（只做参数校验和转发）
│   ├── __init__.py
│   ├── transcribe.py        # POST /api/transcribe
│   ├── analyze.py           # POST /api/analyze
│   ├── feedback.py          # POST /api/feedback
│   ├── context.py           # GET  /api/context
│   ├── memory.py            # GET  /api/memory
│   ├── player.py            # GET  /api/player/status
│   └── music.py             # GET  /api/music/random
│
├── services/                # 业务逻辑层
│   ├── __init__.py
│   ├── whisper_service.py   # faster-whisper 语音转文字
│   ├── emotion_service.py   # LLM 情绪分析
│   ├── context_service.py   # 环境感知采集
│   ├── memory_service.py    # 记忆读写
│   ├── recommender.py       # 推荐算法
│   ├── music_service.py     # 曲库管理
│   └── player_service.py    # mpv 播放器控制
│
├── models/                  # 数据模型
│   ├── __init__.py
│   ├── database.py          # SQLAlchemy engine + session
│   ├── schemas.py           # Pydantic 模型（请求/响应）
│   └── tables.py            # SQLAlchemy 表定义
│
├── music/                   # 本地曲库目录
│   └── *.mp3
│
├── db/                      # 数据库文件
│   └── echopet.db
│
└── tests/                   # 测试
    ├── __init__.py
    ├── conftest.py          # pytest fixtures
    ├── test_transcribe.py
    ├── test_analyze.py
    ├── test_feedback.py
    ├── test_context.py
    ├── test_memory.py
    ├── test_player.py
    └── test_music.py
```

---

## 环境搭建

### 1. 创建虚拟环境

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# API Keys（LLM 情绪分析）
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# faster-whisper
WHISPER_MODEL=base          # tiny / base / small / medium / large
WHISPER_DEVICE=cpu          # cpu / cuda

# mpv
MPV_BINARY=mpv              # mpv 可执行路径，PATH 中有时可省略

# 数据库
DATABASE_URL=sqlite:///db/echopet.db

# 音乐目录
MUSIC_DIR=./music

# 服务
HOST=127.0.0.1
PORT=8000
```

### 4. 启动服务

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

启动后访问 `http://localhost:8000/docs` 查看 Swagger 自动生成文档。

---

## 模块职责

### api/ — 路由层

| 文件 | 职责 | 不负责 |
|------|------|--------|
| transcribe.py | 接收音频 base64，调用 whisper_service，返回文本 | 不做转写逻辑 |
| analyze.py | 接收 text + context，调用 emotion + recommender + player | 不做业务逻辑 |
| feedback.py | 接收反馈、校验枚举值、调用 memory_service | — |
| context.py | 调用 context_service、返回结果 | — |
| memory.py | 解析分页参数、调用 memory_service | — |
| player.py | 调用 player_service 返回 mpv 播放状态 | — |
| music.py | 调用 music_service 返回随机歌曲 | — |

### services/ — 业务逻辑层

| 文件 | 职责 |
|------|------|
| whisper_service.py | 调用 faster-whisper 将 base64 音频 → 转写文本 |
| emotion_service.py | 将文本 + context → 情绪分析结果（调用 LLM） |
| context_service.py | 采集当前环境信息（时间、活跃窗口、键盘频率） |
| memory_service.py | 读写 memory 表，检索相似场景 |
| recommender.py | 根据 context + emotion + memory → 推荐歌曲 |
| music_service.py | 管理曲库（扫描目录、随机取歌、按ID查询） |
| player_service.py | 控制 mpv 播放（play/pause/skip）+ 查询播放状态 |

### models/ — 数据模型层

| 文件 | 职责 |
|------|------|
| database.py | 创建 engine、SessionLocal、初始化表 |
| schemas.py | 定义所有 Pydantic 请求/响应模型 |
| tables.py | 定义 SQLAlchemy ORM 表结构 |

---

## 接口维护清单

| # | 方法 | 路由 | 路由文件 | 核心 Service | 说明 |
|---|------|------|----------|-------------|------|
| 1 | POST | `/api/transcribe` | api/transcribe.py | whisper_service | 音频转文本（faster-whisper） |
| 2 | POST | `/api/analyze` | api/analyze.py | emotion + recommender + player | 文本→情绪→推荐→控制 mpv |
| 3 | POST | `/api/feedback` | api/feedback.py | memory_service | 记录用户反馈 |
| 4 | GET | `/api/context` | api/context.py | context_service | 获取环境上下文 |
| 5 | GET | `/api/memory` | api/memory.py | memory_service | 查询历史记忆（分页） |
| 6 | GET | `/api/player/status` | api/player.py | player_service | 获取 mpv 播放状态 |
| 7 | GET | `/api/music/random` | api/music.py | music_service | 随机返回一首歌 |

---

## 各模块实现方案

### 模块 1：数据库初始化（models/database.py + tables.py）

**database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config import settings

engine = create_engine(settings.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**tables.py**

```python
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from models.database import Base

class Song(Base):
    __tablename__ = "songs"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    tags = Column(Text)            # JSON 字符串: '["lofi","calm"]'
    energy = Column(Float, default=0.5)
    mood = Column(String)
    file_path = Column(String, nullable=False)

class Memory(Base):
    __tablename__ = "memory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    hour = Column(Integer)
    active_app = Column(String)
    kpm = Column(Integer)
    backspace_ratio = Column(Float)
    emotion = Column(String)
    energy = Column(Float)
    song_id = Column(String)
    feedback = Column(String)
```

**schemas.py**

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

# --- 请求模型 ---

class ContextModel(BaseModel):
    hour: int = Field(ge=0, le=23)
    active_app: str
    kpm: int = Field(ge=0)
    backspace_ratio: float = Field(ge=0.0, le=1.0)

class TranscribeRequest(BaseModel):
    audio: str               # base64 编码的音频
    audio_format: str = "wav"

class AnalyzeRequest(BaseModel):
    text: str                # 用户输入文本（直接输入或来自 transcribe）
    input_source: str = Field(pattern="^(text|faster_whisper)$")
    context: ContextModel

class FeedbackRequest(BaseModel):
    song_id: str
    feedback: str = Field(pattern="^(positive|negative|too_quiet|too_sad|more_energy)$")

# --- 响应模型 ---

class TranscribeResponse(BaseModel):
    transcript: str
    language: str = "zh"
    source: str = "faster-whisper"

class EmotionResult(BaseModel):
    emotion: str
    energy: float
    need: str

class SongResponse(BaseModel):
    id: str
    title: str
    artist: str
    tags: list[str]
    energy: float
    mood: str
    file_path: str

class AnalyzeResponse(BaseModel):
    transcript: str
    emotion: EmotionResult
    current_state: str       # idle / focus / tired / frustrated / sad
    bubble_text: str         # 桌宠气泡文案
    assistant_reply: str     # 对用户的回复
    recommendation: SongResponse
    play_action: str         # play / pause / skip / none
    player_status: str       # idle / loading / playing / paused / error

class PlayerStatusResponse(BaseModel):
    player: str = "mpv"
    status: str              # idle / loading / playing / paused / error
    track_id: Optional[str] = None
    title: Optional[str] = None
    artist: Optional[str] = None

class FeedbackResponse(BaseModel):
    status: str = "ok"
    message: str = "Feedback recorded"

class MemoryEntry(BaseModel):
    timestamp: datetime
    context: ContextModel
    emotion: EmotionResult
    song_id: str
    feedback: str

class MemoryResponse(BaseModel):
    entries: list[MemoryEntry]
    total: int
```

---

### 模块 2：Whisper 语音转文字（services/whisper_service.py）

```python
import base64
import tempfile
from faster_whisper import WhisperModel
from config import settings

# 启动时加载模型（避免每次请求都加载）
model = WhisperModel(settings.WHISPER_MODEL, device="cpu", compute_type="int8")

async def transcribe(audio_base64: str, audio_format: str = "wav") -> dict:
    """将 base64 音频转为文本，返回 transcript + language"""
    audio_bytes = base64.b64decode(audio_base64)

    with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name

    segments, info = model.transcribe(temp_path, language="zh", beam_size=5)
    transcript = " ".join([seg.text for seg in segments])

    return {
        "transcript": transcript.strip(),
        "language": info.language
    }
```

**实现要点：**
- `faster-whisper` 本地运行，不依赖外部 API，无网络费用
- 模型启动时加载一次，后续请求复用
- `device="cpu"` 适配无 GPU 环境；有 GPU 可改为 `"cuda"`
- `compute_type="int8"` 降低内存占用，MVP 阶段够用

---

### 模块 3：情绪分析（services/emotion_service.py）

```python
import json
from openai import OpenAI
from config import settings
from models.schemas import ContextModel, EmotionResult

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_PROMPT = """你是一个情绪分析助手。根据用户的语音文本和当前环境上下文，分析用户的情绪状态。

输出严格 JSON 格式：
{
  "emotion": "frustrated|sad|happy|focused|tired|anxious|calm",
  "energy": 0.0~1.0,
  "need": "comfort|focus|energy|relaxation|companionship"
}

energy 参考：
- 0.0~0.3: 低落、疲惫
- 0.3~0.6: 平稳、普通
- 0.6~1.0: 兴奋、亢奋
"""

async def analyze_emotion(text: str, context: ContextModel) -> EmotionResult:
    """调用 LLM 分析情绪"""
    user_message = f"""用户说：{text}

当前环境：
- 时间：{context.hour}点
- 活跃应用：{context.active_app}
- 按键频率：{context.kpm} KPM
- 退格比例：{context.backspace_ratio}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        response_format={"type": "json_object"},
        temperature=0.3
    )

    result = json.loads(response.choices[0].message.content)
    return EmotionResult(**result)
```

**实现要点：**
- `response_format={"type": "json_object"}` 强制 JSON 输出
- `temperature=0.3` 保证结果稳定
- 如使用 Claude，替换为 `anthropic.Anthropic` 的 messages API
- SYSTEM_PROMPT 中定义了枚举值，与接口文档一致

---

### 模块 4：环境感知（services/context_service.py）

```python
import time
import psutil
from datetime import datetime

# Windows: 获取当前活跃窗口
try:
    import win32gui
except ImportError:
    win32gui = None

# 键盘频率追踪
_key_buffer: list[float] = []
_backspace_buffer: list[float] = []
_BUFFER_WINDOW = 60  # 统计最近 60 秒

def get_active_app() -> str:
    """获取当前活跃窗口的进程名"""
    if win32gui is None:
        return "Unknown"
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32gui.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name().replace(".exe", "")
    except Exception:
        return "Unknown"

def get_kpm() -> int:
    """获取最近一分钟的按键频率（需配合键盘钩子）"""
    now = time.time()
    cutoff = now - _BUFFER_WINDOW
    recent = [t for t in _key_buffer if t > cutoff]
    return len(recent)

def get_backspace_ratio() -> float:
    """获取退格键占比"""
    now = time.time()
    cutoff = now - _BUFFER_WINDOW
    all_keys = [t for t in _key_buffer if t > cutoff]
    backspaces = [t for t in _backspace_buffer if t > cutoff]
    if not all_keys:
        return 0.0
    return round(len(backspaces) / len(all_keys), 2)

def record_keypress(is_backspace: bool = False):
    """记录一次按键（由前端或键盘钩子调用）"""
    now = time.time()
    _key_buffer.append(now)
    if is_backspace:
        _backspace_buffer.append(now)
    # 清理过期数据
    cutoff = now - _BUFFER_WINDOW
    _key_buffer[:] = [t for t in _key_buffer if t > cutoff]
    _backspace_buffer[:] = [t for t in _backspace_buffer if t > cutoff]

def get_current_context() -> dict:
    """采集完整的环境上下文"""
    now = datetime.now()
    return {
        "hour": now.hour,
        "active_app": get_active_app(),
        "kpm": get_kpm(),
        "backspace_ratio": get_backspace_ratio()
    }
```

**实现要点：**
- 键盘频率需要全局键盘钩子，MVP 阶段可先由前端定时上报
- Windows 用 `win32gui`，macOS 需替换为 `AppKit`
- `_key_buffer` 为进程内内存，重启后重置（MVP 阶段够用）

---

### 模块 5：推荐器（services/recommender.py）

```python
from sqlalchemy.orm import Session
from models.tables import Memory, Song
from models.schemas import EmotionResult

def recommend(db: Session, emotion: EmotionResult, context: dict) -> Song | None:
    """根据情绪和上下文推荐歌曲"""

    # Step 1: 查询相似场景下的 positive 记忆
    hour = context["hour"]
    hour_range = range(max(0, hour - 2), min(24, hour + 3))  # ±2小时

    positive_memories = db.query(Memory).filter(
        Memory.hour.in_(hour_range),
        Memory.active_app == context["active_app"],
        Memory.feedback == "positive"
    ).all()

    # Step 2: 统计歌曲得分
    song_scores: dict[str, float] = {}
    for mem in positive_memories:
        score = song_scores.get(mem.song_id, 0) + 1
        song_scores[mem.song_id] = score

    # Step 3: 按 energy 匹配排序
    all_songs = db.query(Song).all()
    if not all_songs:
        return None

    ranked = []
    for song in all_songs:
        base_score = song_scores.get(song.id, 0)
        # energy 差异越小，加分越多
        energy_match = 1.0 - abs(song.energy - emotion.energy)
        final_score = base_score + energy_match
        ranked.append((final_score, song))

    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked[0][1] if ranked else None
```

**实现要点：**
- 相似场景定义：±2 小时 + 相同活跃应用
- 无历史数据时，按 energy 最接近的歌曲返回
- 后续可加入 mood 匹配、标签匹配等更复杂的策略

---

### 模块 6：mpv 播放器控制（services/player_service.py）

```python
import mpv
from config import settings

# 初始化 mpv 实例
player = mpv.MPV(
    input_default_bindings=True,
    input_vo_keyboard=True,
    idle=True
)

_current_track: dict | None = None
_status: str = "idle"  # idle / loading / playing / paused / error

def play(file_path: str, track_id: str, title: str, artist: str):
    """播放指定歌曲"""
    global _current_track, _status
    _status = "loading"
    _current_track = {
        "track_id": track_id,
        "title": title,
        "artist": artist
    }
    try:
        player.play(file_path)
        player.wait_for_playing()
        _status = "playing"
    except Exception as e:
        _status = "error"
        print(f"mpv play error: {e}")

def pause():
    """暂停/恢复"""
    global _status
    player.cycle("pause")
    _status = "paused" if _status == "playing" else "playing"

def skip():
    """跳过当前（停止播放）"""
    global _status, _current_track
    player.stop()
    _status = "idle"
    _current_track = None

def get_status() -> dict:
    """获取当前播放状态"""
    return {
        "player": "mpv",
        "status": _status,
        "track_id": _current_track["track_id"] if _current_track else None,
        "title": _current_track["title"] if _current_track else None,
        "artist": _current_track["artist"] if _current_track else None,
    }
```

**实现要点：**
- `python-mpv` 通过 IPC 控制 mpv 进程，无需自己实现播放器
- `idle=True` 让 mpv 启动后不立即退出，等待播放指令
- `wait_for_playing()` 确认播放开始后再更新状态
- 后续可监听 mpv 的 `end-file` 事件实现自动播放下一首

---

### 模块 7：曲库管理（services/music_service.py）

```python
import os
import json
from pathlib import Path
from sqlalchemy.orm import Session
from models.tables import Song
from config import settings

def scan_music_dir(db: Session):
    """扫描音乐目录，将新歌曲入库"""
    music_dir = Path(settings.MUSIC_DIR)
    if not music_dir.exists():
        return

    existing_ids = {s.id for s in db.query(Song.id).all()}
    counter = len(existing_ids)

    for file in music_dir.glob("*.mp3"):
        song_id = f"s{counter:03d}"
        if file.name in {s.file_path.split("/")[-1] for s in db.query(Song).all()}:
            continue

        song = Song(
            id=song_id,
            title=file.stem,
            artist="Unknown",
            tags="[]",
            energy=0.5,
            mood="neutral",
            file_path=f"/music/{file.name}"
        )
        db.add(song)
        counter += 1

    db.commit()

def get_random_song(db: Session) -> Song | None:
    """随机返回一首歌"""
    from sqlalchemy.sql.expression import func
    return db.query(Song).order_by(func.random()).first()

def get_song_by_id(db: Session, song_id: str) -> Song | None:
    """按 ID 查询歌曲"""
    return db.query(Song).filter(Song.id == song_id).first()
```

---

### 模块 8：API 路由示例

**api/transcribe.py**

```python
from fastapi import APIRouter
from models.schemas import TranscribeRequest, TranscribeResponse
from services import whisper_service

router = APIRouter()

@router.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe(req: TranscribeRequest):
    result = await whisper_service.transcribe(req.audio, req.audio_format)
    return TranscribeResponse(
        transcript=result["transcript"],
        language=result["language"],
        source="faster-whisper"
    )
```

**api/analyze.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db
from models.schemas import AnalyzeRequest, AnalyzeResponse
from services import emotion_service, recommender, player_service
from services.memory_service import save_memory

router = APIRouter()

@router.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)):
    # 1. 情绪分析
    emotion = await emotion_service.analyze_emotion(req.text, req.context)

    # 2. 推荐歌曲
    context_dict = req.context.model_dump()
    song = recommender.recommend(db, emotion, context_dict)

    if song is None:
        raise HTTPException(status_code=404, detail="曲库为空，无法推荐")

    # 3. 保存记忆（反馈待用户后续提交）
    save_memory(db, req.context, emotion, song.id)

    # 4. 控制 mpv 播放
    player_service.play(song.file_path, song.id, song.title, song.artist)

    # 5. 生成桌宠状态和文案
    current_state = _map_emotion_to_state(emotion.emotion)
    bubble_text = _generate_bubble_text(emotion)
    assistant_reply = _generate_reply(emotion, song)

    return AnalyzeResponse(
        transcript=req.text,
        emotion=emotion,
        current_state=current_state,
        bubble_text=bubble_text,
        assistant_reply=assistant_reply,
        recommendation={
            "id": song.id,
            "title": song.title,
            "artist": song.artist,
            "tags": song.tags,
            "energy": song.energy,
            "mood": song.mood,
            "file_path": song.file_path,
        },
        play_action="play",
        player_status="loading",
    )

def _map_emotion_to_state(emotion: str) -> str:
    mapping = {
        "frustrated": "frustrated", "sad": "sad", "tired": "tired",
        "anxious": "frustrated", "happy": "focus", "focused": "focus", "calm": "idle",
    }
    return mapping.get(emotion, "idle")

def _generate_bubble_text(emotion) -> str:
    # MVP 阶段用模板，后续可接入 LLM 生成
    templates = {
        "comfort": "你现在有点紧绷，我先放一点柔和的。",
        "focus": "来点专注的音乐吧。",
        "energy": "给你加点能量！",
        "relaxation": "放松一下，听点轻松的。",
        "companionship": "我在这里陪你。",
    }
    return templates.get(emotion.need, "我来给你选首歌。")

def _generate_reply(emotion, song) -> str:
    return f"我感觉你现在需要{emotion.need}，给你放 {song.title}。"
```

**api/player.py**

```python
from fastapi import APIRouter
from models.schemas import PlayerStatusResponse
from services import player_service

router = APIRouter()

@router.get("/api/player/status", response_model=PlayerStatusResponse)
async def get_player_status():
    return player_service.get_status()
```

---

### main.py — 应用入口

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models.database import init_db, SessionLocal
from services.music_service import scan_music_dir
from api import transcribe, analyze, feedback, context, memory, player, music

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    scan_music_dir(db)
    db.close()
    yield

app = FastAPI(title="EchoPet API", version="0.2.0", lifespan=lifespan)

# CORS（DyberPet 前端跨域调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(transcribe.router)
app.include_router(analyze.router)
app.include_router(feedback.router)
app.include_router(context.router)
app.include_router(memory.router)
app.include_router(player.router)
app.include_router(music.router)

@app.get("/")
def root():
    return {"message": "EchoPet Backend Running"}
```

---

## 开发顺序建议

按依赖关系和可测试性排序：

```text
Phase 1 — 基础骨架（Day 1）
├── models/database.py       # 数据库连接
├── models/tables.py         # 表定义
├── models/schemas.py        # Pydantic 模型（7个接口全部定义）
├── config.py                # 配置
├── main.py                  # 入口（含 CORS）
└── 验证：启动服务，访问 /docs 看到空路由

Phase 2 — 静态接口（Day 2）
├── services/music_service.py   # 曲库管理
├── services/context_service.py # 环境感知（先 mock）
├── services/player_service.py  # mpv 控制
├── api/music.py                # GET /api/music/random
├── api/context.py              # GET /api/context
├── api/player.py               # GET /api/player/status
└── 验证：手动放几首 mp3，调通三个 GET 接口

Phase 3 — 核心链路（Day 3-5）
├── services/whisper_service.py  # faster-whisper 语音转文字
├── services/emotion_service.py  # LLM 情绪分析
├── services/recommender.py      # 推荐算法
├── services/memory_service.py   # 记忆读写
├── api/transcribe.py            # POST /api/transcribe
├── api/analyze.py               # POST /api/analyze
├── api/feedback.py              # POST /api/feedback
├── api/memory.py                # GET /api/memory
└── 验证：完整链路 transcribe → analyze → player/status → feedback

Phase 4 — 打磨（Day 6）
├── 错误处理完善
├── 接口参数校验补全
├── 单元测试编写
├── 键盘钩子集成（环境感知增强）
└── 验证：所有接口通过测试，/docs 文档完整
```

---

## 注意事项

1. **CORS**：DyberPet 前端通过 HTTP 调用后端，已在 main.py 配置 CORS 中间件
2. **faster-whisper**：本地部署，无 API 费用；首次启动需下载模型（~140MB for base），之后缓存本地
3. **mpv 依赖**：需确保系统已安装 mpv，`python-mpv` 通过 IPC 与之通信
4. **曲库目录**：music/ 目录需手动放入 mp3 文件，file_path 存绝对路径供 mpv 直接播放
5. **SQLite 并发**：SQLite 写操作串行，MVP 阶段够用；用户量增长后迁移 PostgreSQL
6. **键盘监听**：`win32gui` 仅支持 Windows，跨平台需条件判断
