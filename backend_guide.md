# EchoPet 后端开发指南

> 本文档为后端开发者提供完整的开发指导，包括技术栈、文件结构、模块职责和实现方案。

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
| 语音转文字 | OpenAI Whisper | 本地部署或 API 调用 |
| 情绪分析 | OpenAI GPT / Claude | LLM 推理 |
| 音频处理 | pydub / ffmpeg | 音频格式转换 |
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
openai          # Whisper + GPT
anthropic       # Claude（可选）
psutil
pydub
pytest
httpx
python-multipart   # 文件上传支持
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
│   ├── analyze.py           # POST /api/analyze
│   ├── feedback.py          # POST /api/feedback
│   ├── context.py           # GET  /api/context
│   ├── memory.py            # GET  /api/memory
│   └── music.py             # GET  /api/music/random
│
├── services/                # 业务逻辑层
│   ├── __init__.py
│   ├── whisper_service.py   # Whisper 语音转文字
│   ├── emotion_service.py   # LLM 情绪分析
│   ├── context_service.py   # 环境感知采集
│   ├── memory_service.py    # 记忆读写
│   ├── recommender.py       # 推荐算法
│   └── music_service.py     # 曲库管理
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
    ├── test_analyze.py
    ├── test_feedback.py
    ├── test_context.py
    ├── test_memory.py
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
# API Keys
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# Whisper
WHISPER_MODEL=base          # tiny / base / small / medium / large

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
| analyze.py | 接收请求、校验参数、调用 services、返回响应 | 不做业务逻辑 |
| feedback.py | 接收反馈、校验枚举值、调用 memory_service | — |
| context.py | 调用 context_service、返回结果 | — |
| memory.py | 解析分页参数、调用 memory_service | — |
| music.py | 调用 music_service 返回随机歌曲 | — |

### services/ — 业务逻辑层

| 文件 | 职责 |
|------|------|
| whisper_service.py | 将 base64 音频 → 转写文本 |
| emotion_service.py | 将文本 + context → 情绪分析结果（调用 LLM） |
| context_service.py | 采集当前环境信息（时间、活跃窗口、键盘频率） |
| memory_service.py | 读写 memory 表，检索相似场景 |
| recommender.py | 根据 context + emotion + memory → 推荐歌曲 |
| music_service.py | 管理曲库（扫描目录、随机取歌、按ID查询） |

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
| 1 | POST | `/api/analyze` | api/analyze.py | whisper + emotion + recommender | 核心接口，语音→情绪→推荐 |
| 2 | POST | `/api/feedback` | api/feedback.py | memory_service | 记录用户反馈 |
| 3 | GET | `/api/context` | api/context.py | context_service | 获取环境上下文 |
| 4 | GET | `/api/memory` | api/memory.py | memory_service | 查询历史记忆（分页） |
| 5 | GET | `/api/music/random` | api/music.py | music_service | 随机返回一首歌 |

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

class AnalyzeRequest(BaseModel):
    audio: str              # base64 编码的音频
    context: ContextModel

class FeedbackRequest(BaseModel):
    song_id: str
    feedback: str = Field(pattern="^(positive|negative|too_quiet|too_sad|more_energy)$")

# --- 响应模型 ---

class EmotionResult(BaseModel):
    emotion: str
    energy: float
    need: str

class SongResponse(BaseModel):
    id: str
    title: str
    artist: str
    file_path: str

class AnalyzeResponse(BaseModel):
    transcript: str
    emotion: EmotionResult
    recommendation: SongResponse

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
from openai import OpenAI
from config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def transcribe(audio_base64: str) -> str:
    """将 base64 音频转为文本"""
    audio_bytes = base64.b64decode(audio_base64)

    # 写入临时文件（Whisper API 需要文件对象）
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name

    with open(temp_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model=settings.WHISPER_MODEL,
            file=f,
            language="zh"
        )

    return result.text
```

**实现要点：**
- 支持 wav / mp3 / m4a 格式，Whisper 自动识别
- `language="zh"` 指定中文，提升识别准确率
- 后续可改为本地 Whisper 模型部署，避免 API 费用

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

### 模块 6：曲库管理（services/music_service.py）

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

### 模块 7：API 路由示例（api/analyze.py）

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.database import get_db
from models.schemas import AnalyzeRequest, AnalyzeResponse
from services import whisper_service, emotion_service, context_service, recommender

router = APIRouter()

@router.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)):
    # 1. 语音转文字
    transcript = await whisper_service.transcribe(req.audio)

    # 2. 情绪分析
    emotion = await emotion_service.analyze_emotion(transcript, req.context)

    # 3. 推荐歌曲
    context_dict = req.context.model_dump()
    song = recommender.recommend(db, emotion, context_dict)

    if song is None:
        raise HTTPException(status_code=404, detail="曲库为空，无法推荐")

    # 4. 保存记忆
    from services.memory_service import save_memory
    save_memory(db, req.context, emotion, song.id)

    return AnalyzeResponse(
        transcript=transcript,
        emotion=emotion,
        recommendation={
            "id": song.id,
            "title": song.title,
            "artist": song.artist,
            "file_path": song.file_path
        }
    )
```

---

### main.py — 应用入口

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from models.database import init_db
from services.music_service import scan_music_dir
from models.database import SessionLocal
from api import analyze, feedback, context, memory, music

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化
    init_db()
    db = SessionLocal()
    scan_music_dir(db)
    db.close()
    yield

app = FastAPI(
    title="EchoPet API",
    version="0.1.0",
    lifespan=lifespan
)

# 挂载路由
app.include_router(analyze.router)
app.include_router(feedback.router)
app.include_router(context.router)
app.include_router(memory.router)
app.include_router(music.router)

@app.get("/")
def root():
    return {"message": "EchoPet Backend Running"}
```

---

## 开发顺序建议

按依赖关系和可测试性排序：

```
Phase 1 — 基础骨架（Day 1-2）
├── models/database.py       # 数据库连接
├── models/tables.py         # 表定义
├── models/schemas.py        # Pydantic 模型
├── config.py                # 配置
├── main.py                  # 入口
└── 验证：启动服务，访问 /docs 看到空路由

Phase 2 — 静态接口（Day 3-4）
├── services/music_service.py   # 曲库管理
├── services/context_service.py # 环境感知（先 mock）
├── api/music.py                # GET /api/music/random
├── api/context.py              # GET /api/context
└── 验证：手动放几首 mp3，调通这两个 GET 接口

Phase 3 — 核心链路（Day 5-8）
├── services/whisper_service.py  # 语音转文字
├── services/emotion_service.py  # 情绪分析
├── services/recommender.py      # 推荐算法
├── services/memory_service.py   # 记忆读写
├── api/analyze.py               # POST /api/analyze
├── api/feedback.py              # POST /api/feedback
├── api/memory.py                # GET /api/memory
└── 验证：用真实音频测试完整链路 analyze → feedback

Phase 4 — 打磨（Day 9-10）
├── 错误处理完善
├── 接口参数校验补全
├── 单元测试编写
├── 键盘钩子集成（环境感知增强）
└── 验证：所有接口通过测试，/docs 文档完整
```

---

## 注意事项

1. **CORS**：前端 Electron/Tauri 通过 HTTP 调用后端，需在 main.py 添加 CORS 中间件
2. **Whisper 成本**：API 调用按音频时长计费，MVP 阶段可用 `tiny` 模型降低成本
3. **曲库目录**：music/ 目录需手动放入 mp3 文件，或提供上传接口
4. **SQLite 并发**：SQLite 写操作串行，MVP 阶段够用；用户量增长后迁移 PostgreSQL
5. **键盘监听**：`win32gui` 仅支持 Windows，跨平台需条件判断
