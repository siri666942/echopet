# EchoPet 后端开发指南

> 本文档为后端开发者的日常工作指南，涵盖技术栈、文件结构、模块职责、接口实现和开发流程。

---

## 目录

- [技术栈](#技术栈)
- [文件结构](#文件结构)
- [模块职责](#模块职责)
- [接口清单](#接口清单)
- [各模块实现指南](#各模块实现指南)
  - [1. 环境感知模块](#1-环境感知模块-environment)
  - [2. 语音转写模块](#2-语音转写模块-whisper)
  - [3. 情绪分析模块](#3-情绪分析模块-emotion)
  - [4. 推荐模块](#4-推荐模块-recommender)
  - [5. 记忆模块](#5-记忆模块-memory)
  - [6. 曲库管理模块](#6-曲库管理模块-music)
- [开发流程](#开发流程)
- [环境变量](#环境变量)

---

## 技术栈


| 组件     | 技术                      | 用途            |
| ------ | ----------------------- | ------------- |
| Web 框架 | **FastAPI**             | HTTP 接口服务     |
| 语言     | **Python 3.11+**        | 后端主语言         |
| 数据库    | **SQLite**              | 本地存储（歌曲、记忆）   |
| ORM    | **SQLAlchemy**          | 数据库操作         |
| 语音转写   | **OpenAI Whisper**      | 语音 → 文本       |
| 情绪分析   | **OpenAI GPT / Claude** | 文本 + 上下文 → 情绪 |
| 音频处理   | **FFmpeg**              | 音频格式转换        |
| 数据校验   | **Pydantic**            | 请求/响应模型       |


---

## 文件结构

```
echopet/
├── backend/
│   ├── main.py                 # FastAPI 入口，挂载路由
│   ├── config.py               # 配置管理（环境变量、路径）
│   ├── requirements.txt        # Python 依赖
│   │
│   ├── api/                    # 路由层（只做参数校验和转发）
│   │   ├── __init__.py
│   │   ├── analyze.py          # POST /api/analyze
│   │   ├── feedback.py         # POST /api/feedback
│   │   ├── context.py          # GET  /api/context
│   │   ├── memory.py           # GET  /api/memory
│   │   └── music.py            # GET  /api/music/random
│   │
│   ├── services/               # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── environment.py      # 环境感知（时间、应用、键盘）
│   │   ├── whisper.py          # Whisper 语音转写
│   │   ├── emotion.py          # LLM 情绪分析
│   │   ├── recommender.py      # 推荐算法
│   │   ├── memory.py           # 记忆读写
│   │   └── music.py            # 曲库管理
│   │
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── database.py         # SQLAlchemy 引擎和 Session
│   │   ├── song.py             # Song 表模型
│   │   └── memory.py           # Memory 表模型
│   │
│   ├── schemas/                # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   ├── analyze.py
│   │   ├── feedback.py
│   │   ├── context.py
│   │   ├── memory.py
│   │   └── music.py
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       └── audio.py            # 音频 Base64 解码、格式转换
│
├── data/                       # 运行时数据（gitignore）
│   ├── echopet.db              # SQLite 数据库
│   └── music/                  # 本地曲库
│       └── s001.mp3
│
├── api_docs.md                 # 接口文档
├── product_design.md
├── techneque_design.md
└── README.md
```

---

## 模块职责

后端**负责**：

- Whisper 语音转写调用
- LLM 情绪分析调用
- 环境感知（时间、当前应用）
- Memory 读写和检索
- 推荐算法
- 曲库管理

后端**不负责**：

- 桌宠 UI 渲染
- 录音采集（前端负责）
- 音乐播放（前端负责）
- 键盘节奏采集（前端负责，通过 context 传入）

---

## 接口清单


| #   | 方法   | 路由                  | 模块                              | 说明              |
| --- | ---- | ------------------- | ------------------------------- | --------------- |
| 1   | POST | `/api/analyze`      | whisper + emotion + recommender | 核心：语音 → 情绪 → 推荐 |
| 2   | POST | `/api/feedback`     | memory                          | 记录用户反馈          |
| 3   | GET  | `/api/context`      | environment                     | 返回当前环境上下文       |
| 4   | GET  | `/api/memory`       | memory                          | 查询历史记忆（分页）      |
| 5   | GET  | `/api/music/random` | music                           | 随机返回一首歌         |


详细请求/响应格式见 [api_docs.md](api_docs.md)。

---

## 各模块实现指南

### 1. 环境感知模块 (`services/context_service.py`)

**职责**：采集后端可获取的环境信息（hour、active_app），接收前端传入的键盘数据（kpm、backspace_ratio），组装 Context 对象。

**字段来源**：

| 字段 | 来源 | 说明 |
|------|------|------|
| hour | 后端 | 系统时间 |
| active_app | 后端 | Windows 前台窗口（pywin32） |
| kpm | **前端** | 前端采集后通过 query 参数传入 |
| backspace_ratio | **前端** | 前端采集后通过 query 参数传入 |

**实现思路**：

```python
# services/context_service.py

from datetime import datetime

def get_current_context(kpm: int = 0, backspace_ratio: float = 0.0) -> dict:
    return {
        "hour": datetime.now().hour,
        "active_app": get_active_app(),
        "kpm": kpm,                    # 前端传入，不传默认 0
        "backspace_ratio": backspace_ratio,  # 前端传入，不传默认 0.0
    }

def get_active_app() -> str:
    """获取当前前台应用名称"""
    try:
        import psutil
        import win32gui
        import win32process
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name().replace(".exe", "")
    except Exception:
        return "Unknown"
```

**依赖**：`psutil`、`pywin32`（Windows）

**调用方式**：

- `GET /api/context?kpm=160&backspace_ratio=0.22` — 前端通过 query 参数传入
- `POST /api/analyze` — 前端在请求体 `context` 字段中直接传入

---

### 2. 语音转写模块 (`services/whisper.py`)

**职责**：接收音频 Base64，调用 Whisper 返回文本。

**实现思路**：

```python
# services/whisper.py

import whisper

model = whisper.load_model("base")  # 首次启动时加载，常驻内存

def transcribe(audio_bytes: bytes) -> str:
    """
    接收音频字节流，返回转写文本。
    Whisper 要求输入为 16kHz WAV。
    """
    import tempfile, os
    # 写入临时文件
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        result = model.transcribe(tmp_path, language="zh")
        return result["text"]
    finally:
        os.unlink(tmp_path)
```

**依赖**：`openai-whisper`、`ffmpeg`（需系统安装）

**模型选择**：


| 模型     | 大小    | 速度  | 精度  | 建议         |
| ------ | ----- | --- | --- | ---------- |
| tiny   | 39MB  | 最快  | 低   | 开发调试       |
| base   | 74MB  | 快   | 中   | **MVP 推荐** |
| small  | 244MB | 中   | 高   | 生产环境       |
| medium | 769MB | 慢   | 很高  | 按需         |


---

### 3. 情绪分析模块 (`services/emotion.py`)

**职责**：根据转写文本 + 环境上下文 + 历史记忆，调用 LLM 分析情绪。

**实现思路**：

```python
# services/emotion.py

from openai import OpenAI

client = OpenAI()  # 读取 OPENAI_API_KEY 环境变量

SYSTEM_PROMPT = """你是一个情绪分析助手。根据用户的语音文本和当前环境，分析其情绪状态。

输出 JSON 格式：
{
  "emotion": "frustrated|sad|happy|focused|tired|anxious|calm",
  "energy": 0.0~1.0,
  "need": "comfort|focus|energy|relaxation|companionship"
}

规则：
- energy 0 表示极度低落/疲惫，1 表示亢奋/高能量
- need 表示用户此刻最需要什么
- 只输出 JSON，不要解释"""

def analyze_emotion(
    transcript: str,
    context: dict,
    memory_context: str = ""
) -> dict:
    """
    调用 LLM 分析情绪。
    """
    user_message = f"""用户说："{transcript}"

当前环境：
- 时间：{context.get('hour')}点
- 当前应用：{context.get('active_app')}
- 按键频率：{context.get('kpm')} KPM
"""

    if memory_context:
        user_message += f"\n历史记忆：\n{memory_context}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # 成本低、速度快
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    import json
    return json.loads(response.choices[0].message.content)
```

**依赖**：`openai`

**成本参考**（GPT-4o-mini）：约 $0.15 / 1M input tokens，每次分析约 200 tokens ≈ $0.00003

---

### 4. 推荐模块 (`services/recommender.py`)

**职责**：根据情绪和上下文，从曲库中推荐最合适的歌曲。

**实现思路**：

```python
# services/recommender.py

from sqlalchemy.orm import Session
from models.song import Song
from models.memory import MemoryEntry

def recommend(
    db: Session,
    context: dict,
    emotion: dict,
) -> dict:
    """
    推荐算法：
    1. 检索相似场景的记忆
    2. 统计 positive 反馈的歌曲
    3. 按 energy 匹配
    4. 返回最佳歌曲
    """
    # Step 1: 相似场景记忆
    hour = context.get("hour", 12)
    active_app = context.get("active_app", "")
    hour_range = range(max(0, hour - 2), min(24, hour + 3))  # ±2小时

    similar_memories = db.query(MemoryEntry).filter(
        MemoryEntry.hour.in_(hour_range),
        MemoryEntry.active_app == active_app,
        MemoryEntry.feedback == "positive",
    ).all()

    # Step 2: 统计歌曲得分
    song_scores: dict[str, int] = {}
    for m in similar_memories:
        song_scores[m.song_id] = song_scores.get(m.song_id, 0) + 1

    # Step 3: 如果有历史偏好，优先推荐
    target_energy = emotion.get("energy", 0.5)

    if song_scores:
        # 在偏好歌曲中找 energy 最接近的
        preferred_ids = list(song_scores.keys())
        songs = db.query(Song).filter(Song.id.in_(preferred_ids)).all()
        songs.sort(key=lambda s: abs(s.energy - target_energy))
        return songs[0]

    # Step 4: 无历史记忆，按 energy 匹配全库
    all_songs = db.query(Song).all()
    if not all_songs:
        return None

    all_songs.sort(key=lambda s: abs(s.energy - target_energy))
    return all_songs[0]
```

---

### 5. 记忆模块 (`services/memory.py`)

**职责**：读写记忆条目，支持分页查询。

**实现思路**：

```python
# services/memory.py

from datetime import datetime
from sqlalchemy.orm import Session
from models.memory import MemoryEntry

def save_memory(
    db: Session,
    context: dict,
    emotion: dict,
    song_id: str,
    feedback: str = None,
) -> MemoryEntry:
    """保存一条记忆"""
    entry = MemoryEntry(
        timestamp=datetime.now(),
        hour=context.get("hour"),
        active_app=context.get("active_app"),
        kpm=context.get("kpm", 0),
        backspace_ratio=context.get("backspace_ratio", 0.0),
        emotion=emotion.get("emotion"),
        energy=emotion.get("energy"),
        song_id=song_id,
        feedback=feedback,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_memories(
    db: Session,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[MemoryEntry], int]:
    """分页查询记忆"""
    total = db.query(MemoryEntry).count()
    entries = db.query(MemoryEntry)\
        .order_by(MemoryEntry.timestamp.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    return entries, total

def get_memory_context(db: Session, context: dict) -> str:
    """获取与当前场景相关的历史记忆摘要（供 LLM 参考）"""
    hour = context.get("hour", 12)
    active_app = context.get("active_app", "")
    hour_range = range(max(0, hour - 2), min(24, hour + 3))

    recent = db.query(MemoryEntry).filter(
        MemoryEntry.hour.in_(hour_range),
        MemoryEntry.active_app == active_app,
    ).order_by(MemoryEntry.timestamp.desc()).limit(5).all()

    if not recent:
        return ""

    lines = []
    for m in recent:
        lines.append(
            f"- {m.timestamp}: 情绪={m.emotion}, energy={m.energy}, "
            f"歌曲={m.song_id}, 反馈={m.feedback}"
        )
    return "\n".join(lines)
```

---

### 6. 曲库管理模块 (`services/music.py`)

**职责**：管理本地曲库，提供查询和随机获取。

**实现思路**：

```python
# services/music.py

import random
from sqlalchemy.orm import Session
from models.song import Song

def get_random_song(db: Session) -> Song | None:
    """随机返回一首歌"""
    songs = db.query(Song).all()
    if not songs:
        return None
    return random.choice(songs)

def get_song_by_id(db: Session, song_id: str) -> Song | None:
    """按 ID 获取歌曲"""
    return db.query(Song).filter(Song.id == song_id).first()

def init_sample_songs(db: Session):
    """初始化示例曲库（开发用）"""
    samples = [
        Song(id="s001", title="Midnight Rain", artist="LoFi Dreams",
             tags='["lofi","calm","night"]', energy=0.3, mood="soothing",
             file_path="/music/s001.mp3"),
        Song(id="s002", title="Deep Focus", artist="Ambient Works",
             tags='["ambient","focus"]', energy=0.5, mood="focused",
             file_path="/music/s002.mp3"),
        Song(id="s003", title="Sunrise Energy", artist="Morning Beats",
             tags='["upbeat","morning"]', energy=0.8, mood="energetic",
             file_path="/music/s003.mp3"),
        # ... 按需添加
    ]
    for song in samples:
        db.merge(song)  # merge 避免重复插入
    db.commit()
```

---

## 开发流程

### 第一步：环境搭建

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**requirements.txt 内容**：

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
pydantic==2.9.0
openai==1.50.0
openai-whisper==20231117
psutil==6.0.0
pywin32==306; sys_platform == "win32"
```

### 第二步：初始化数据库

```bash
python -c "from models.database import init_db; init_db()"
```

### 第三步：启动服务

```bash
uvicorn main:app --reload --port 8000
```

访问 `http://localhost:8000/docs` 查看自动生成的 Swagger 文档。

### 第四步：开发顺序

建议按以下顺序开发，每完成一步即可联调：


| 顺序  | 模块       | 接口                                       | 说明           |
| --- | -------- | ---------------------------------------- | ------------ |
| ①   | 曲库 + 数据库 | `GET /api/music/random`                  | 先跑通数据库和基础接口  |
| ②   | 环境感知     | `GET /api/context`                       | 简单，验证环境采集    |
| ③   | 记忆模块     | `GET /api/memory` + `POST /api/feedback` | 数据读写         |
| ④   | Whisper  | —                                        | 先单独验证语音转写    |
| ⑤   | 情绪分析     | —                                        | 先单独验证 LLM 调用 |
| ⑥   | 推荐算法     | —                                        | 组合记忆 + 曲库    |
| ⑦   | 核心接口     | `POST /api/analyze`                      | 串联全部模块       |


---

## 环境变量

在项目根目录创建 `.env` 文件：

```env
# LLM
OPENAI_API_KEY=sk-xxx
# 或使用 Claude
# ANTHROPIC_API_KEY=sk-ant-xxx

# Whisper
WHISPER_MODEL=base

# 数据库
DATABASE_URL=sqlite:///data/echopet.db

# 音乐目录
MUSIC_DIR=./data/music
```

---

## 接口路由示例 (`main.py`)

```python
# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import analyze, feedback, context, memory, music
from models.database import init_db

app = FastAPI(title="EchoPet API", version="0.1.0")

# CORS — 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为前端域名
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时初始化数据库
@app.on_event("startup")
def startup():
    init_db()

# 挂载路由
app.include_router(analyze.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(context.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(music.router, prefix="/api")

@app.get("/")
def root():
    return {"service": "EchoPet API", "version": "0.1.0"}
```

---

## 变更记录


| 日期         | 版本   | 说明   |
| ---------- | ---- | ---- |
| 2026-05-30 | v0.1 | 初始版本 |


