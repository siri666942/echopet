# EchoPet

> Not just music. A companion that understands your moment.
>
> 不只是音乐，而是懂你此刻状态的桌面音乐伙伴。

EchoPet 是一个本地优先的桌面情绪音乐 Agent。它把 DyberPet 桌宠、语音输入、环境上下文、长期记忆和本地曲库推荐连接起来：用户不需要打开音乐软件反复搜索，只要对桌宠说一句“我现在有点烦”或“我想专注一下”，EchoPet 就会理解当下状态，并从本地音乐库里推荐更适合此刻的音乐。

![EchoPet 主界面](./主界面.png)

## 目录

- [项目能做什么](#项目能做什么)
- [为什么做 EchoPet](#为什么做-echopet)
- [产品体验](#产品体验)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [Quick Start](#quick-start)
- [曲库管理](#曲库管理)
- [配置说明](#配置说明)
- [开发与测试](#开发与测试)
- [常见问题](#常见问题)
- [项目结构](#项目结构)
- [Roadmap](#roadmap)

## 项目能做什么

EchoPet 的核心不是“播放一首歌”，而是理解用户为什么此刻需要音乐。

| 能力 | 说明 |
| --- | --- |
| 桌面伙伴 | 基于 DyberPet 的桌宠形态，常驻桌面，低打扰、轻交互。 |
| 文本与语音输入 | 支持文本输入，也支持录音后通过 faster-whisper 转写。 |
| 环境感知 | 结合时间、活跃应用、键盘节奏等弱信号判断用户场景。 |
| 情绪与意图分析 | 将用户表达转成当前状态、需求和音乐检索意图。 |
| 本地曲库推荐 | 扫描本地曲库，用真实音频特征和 embedding 做语义召回。 |
| 播放反馈 | 记录完成率、跳过等隐式反馈，沉淀用户偏好。 |
| 长期记忆 | 从历史交互中学习“什么场景下适合什么音乐”。 |

## 为什么做 EchoPet

传统音乐产品知道用户“听过什么”，但通常不知道用户“为什么现在需要这首歌”。EchoPet 试图把推荐目标从“相似歌曲”前移到“当前状态”：

- 深夜写代码时，需要的是不抢注意力的稳定节奏。
- Debug 卡住时，需要的是能降低烦躁感的缓冲。
- 学习或写论文时，需要的是维持心流，而不是强刺激。
- 情绪低落时，需要的是被理解后的陪伴感。

EchoPet 的产品假设是：音乐只是结果，理解才是核心。

## 产品体验

EchoPet 采用桌宠作为入口，而不是传统播放器窗口。用户可以通过右键菜单打开 EchoPet 面板，输入文字或录音，拿到一首推荐和一段桌宠回应。

![EchoPet](./1.png)

典型流程：

```text
用户输入一句话或录音
  -> 前端采集环境上下文和键盘节奏
  -> 后端分析当前状态与音乐需求
  -> 生成 retrieval query
  -> 本地曲库 embedding 召回
  -> mpv 播放推荐歌曲
  -> 桌宠显示状态、气泡和推荐卡片
  -> 用户 KEEP / SKIP 反馈进入长期画像
```

当前支持的桌宠状态包括：

| 状态 | 含义 | 典型场景 |
| --- | --- | --- |
| `idle` | 待机 | 没有明确输入或播放状态 |
| `focus` | 专注 | 写代码、学习、持续输入 |
| `happy` | 积极 | 轻松、状态不错 |
| `tired` | 疲惫 | 深夜、低能量但还想继续 |
| `frustrated` | 烦躁 | Debug、卡住、高退格比例 |
| `sad` | 低落 | 情绪低沉、需要陪伴 |

## 系统架构

EchoPet 采用“Windows 本地桌宠 + Docker 后端”的混合架构：

```text
┌──────────────────────────────────────────────────────────┐
│ Windows 桌面端                                            │
│                                                          │
│  DyberPet / PySide6                                      │
│  - 桌宠主窗口                                             │
│  - EchoPet 输入面板                                       │
│  - 键盘节奏采集                                           │
│  - 本地播放控制                                           │
└──────────────────────────────┬───────────────────────────┘
                               │ HTTP / JSON
┌──────────────────────────────▼───────────────────────────┐
│ FastAPI 后端                                               │
│                                                          │
│  /api/transcribe    faster-whisper 语音转写               │
│  /api/context       环境上下文                             │
│  /api/analyze       情绪、意图和推荐                        │
│  /api/player/*      播放状态与反馈                          │
│  /api/memory        记忆数据查看                            │
└──────────────────────────────┬───────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────┐
│ 本地智能层                                                 │
│                                                          │
│  Essentia TensorFlow 音频特征                             │
│  BAAI/bge-small-zh-v1.5 本地 embedding                    │
│  SQLite 记忆、歌曲、会话、反馈                             │
│  mpv 播放器                                                │
└──────────────────────────────────────────────────────────┘
```

推荐主链路：

```text
文本 + 环境上下文 + 键盘事件
  -> intent_service / emotion_service
  -> retrieval_query
  -> recommender embedding search
  -> playlist_service
  -> player_service
  -> play_session_service / profile_service
```

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 桌面端 UI | Python, PySide6, PySide6-Fluent-Widgets, DyberPet |
| 后端 API | FastAPI, Pydantic, Uvicorn |
| 语音转写 | faster-whisper |
| 音频分析 | Essentia TensorFlow models |
| 语义召回 | fastembed, BAAI/bge-small-zh-v1.5 |
| 数据库 | SQLite, SQLAlchemy |
| 播放器 | mpv |
| 运行环境 | 后端 Docker Compose，前端 Windows Python venv |
| 测试 | pytest |

## Quick Start

推荐运行方式：

```text
后端：Docker 跑 Linux 环境，负责 Essentia、embedding、曲库、API
前端：Windows 本地 Python venv 跑 DyberPet 桌宠
```

不推荐用 Windows 本地 venv 跑后端主链路。真实歌曲入库需要 `essentia-tensorflow`，它在 Windows + Python 3.11 下没有稳定可用的 PyPI wheel；Docker 里的 Linux 环境已经验证可用。

### 前置依赖

- Windows
- Docker Desktop
- Python 3.11
- PowerShell

### 一键启动

在项目根目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_echopet.ps1
```

这个脚本会：

1. 启动 Docker 后端。
2. 等待 `http://127.0.0.1:8000` 可用。
3. 准备 faster-whisper 模型。
4. 检查 `backend/music/` 是否有新音乐。
5. 曲库变化时自动重建索引。
6. 准备并启动 DyberPet 前端。

停止前后端：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop_echopet.ps1
```

### 常用启动参数

后端依赖、Dockerfile 或代码变化后重新构建：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_echopet.ps1 -Build
```

强制重扫曲库：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_echopet.ps1 -ForceReindex
```

首次安装或更新前端依赖：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_echopet.ps1 -InstallFrontendDeps
```

使用本地后端开发模式：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_echopet.ps1 -LocalBackend -InstallBackendDeps
```

### 验证后端

```powershell
Invoke-WebRequest http://127.0.0.1:8000/
```

正常返回：

```json
{"service":"EchoPet API","version":"0.2.0"}
```

Swagger 文档：

```text
http://127.0.0.1:8000/docs
```

### 首次准备模型

后端不会写假音频特征，也不会写假向量。真实歌曲入库前，需要准备两类模型：

| 模型 | 用途 | 保存位置 |
| --- | --- | --- |
| Essentia TensorFlow models | 分析歌曲节奏、响度、调性、情绪、风格等音频特征。 | `backend/models/essentia/` |
| 本地 embedding 模型 | 把歌曲描述和用户需求转成向量，用于语义召回。 | `backend/models/fastembed/` |

第一次跑项目时执行：

```powershell
python -m backend.scripts.download_essentia_models
docker compose exec echopet-backend python -c "from backend.services.embedding_service import embed_text; print(len(embed_text('测试中文向量')))"
```

第二条命令正常会输出：

```text
512
```

这些模型文件较大，不提交 git；下载后会留在本地 `backend/models/`，除非删除目录，否则不用重复准备。

### 使用 EchoPet

1. 运行 `scripts/start_echopet.ps1`。
2. 桌面上出现桌宠后，右键点击桌宠。
3. 点击菜单中的 `OPEN ECHOPET`。
4. 在 EchoPet 面板里输入一句话，或点击录音按钮说话。
5. 等待后端返回状态、气泡文案和推荐歌曲。
6. 使用 `KEEP` / `SKIP` 等反馈按钮，让系统记录这次推荐是否合适。

## 曲库管理

把音乐文件放到：

```text
backend/music/
```

支持格式：

```text
.mp3
.wav
.flac
```

手动重扫曲库：

```powershell
docker compose exec echopet-backend python -m backend.scripts.reindex_music
```

按当前 `backend/music/` 完全重建曲库记录：

```powershell
docker compose exec echopet-backend python -m backend.scripts.reindex_music --reset
```

查看入库结果：

```powershell
docker compose exec echopet-backend python -c "from backend.models.database import SessionLocal; from backend.models.tables import Song, SongIngestFailure; db=SessionLocal(); print('songs=', db.query(Song).count()); print('failures=', db.query(SongIngestFailure).count()); db.close()"
```

模型文件会保存在 `backend/models/`。这些文件较大，不提交 git，但本地保留后无需每次重复下载。

## 配置说明

项目根目录 `.env` 主要放聊天模型配置：

```env
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.stepfun.com/v1
OPENAI_MODEL=step-3.7-flash
```

embedding 默认走本地模型：

```env
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

如果有支持 `/v1/embeddings` 的 OpenAI 兼容服务，可以切换为：

```env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=provider_embedding_model
```

常用后端环境变量：

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `OPENAI_API_KEY` | empty | 聊天模型 API key。为空时部分逻辑会走规则兜底。 |
| `OPENAI_BASE_URL` | empty | OpenAI 兼容 API 地址。 |
| `OPENAI_MODEL` | `gpt-4o-mini` | 聊天模型名。 |
| `EMBEDDING_PROVIDER` | `local` | `local` 或 `openai`。 |
| `LOCAL_EMBEDDING_MODEL` | `BAAI/bge-small-zh-v1.5` | 本地中文 embedding 模型。 |
| `WHISPER_MODEL_DIR` | `backend/models/faster-whisper` | faster-whisper 模型目录。 |
| `ENABLE_MPV` | `true` | Docker 默认关闭真实 mpv 播放，本地后端可开启。 |

## 开发与测试

### 后端

手动启动 Docker 后端：

```powershell
docker compose up -d --build
```

查看日志：

```powershell
docker compose logs -f echopet-backend
```

运行后端测试：

```powershell
python -m pytest backend/tests
```

Docker 内运行测试：

```powershell
docker compose exec echopet-backend python -m pytest backend/tests
```

### 前端

首次安装前端依赖：

```powershell
python -m venv DyberPet-main/.venv
DyberPet-main/.venv/Scripts/pip install -r DyberPet-main/requirements.txt
```

手动启动前端时，需要先进入前端目录：

```powershell
cd DyberPet-main
.venv/Scripts/python run_DyberPet.py
```

不要从项目根目录直接执行 `DyberPet-main/run_DyberPet.py`，否则 DyberPet 会找不到 `res/language/language.json` 等相对路径资源。

前端语法检查：

```powershell
DyberPet-main/.venv/Scripts/python -m compileall DyberPet-main/frontend DyberPet-main/DyberPet/DyberPet.py
```

### API

核心接口详见 [api_docs.md](./api_docs.md)。

常用接口：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `POST` | `/api/transcribe` | 录音转文本 |
| `GET` | `/api/context` | 获取环境上下文 |
| `POST` | `/api/analyze` | 分析状态并生成推荐 |
| `GET` | `/api/player/status` | 查询播放状态 |
| `POST` | `/api/player/event` | 上报播放完成、跳过等反馈 |
| `POST` | `/api/player/pause` | 暂停或继续 |
| `POST` | `/api/player/skip` | 切到下一首 |
| `GET` | `/api/memory` | 查看记忆数据 |

## 常见问题

### 8000 端口被占用

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

停止占用端口的进程：

```powershell
Stop-Process -Id <PID> -Force
```

### 曲库入库失败

常见原因：

| 原因 | 处理方式 |
| --- | --- |
| 模型未准备好 | 重新运行 `scripts/start_echopet.ps1`，或手动执行模型下载脚本。 |
| 数据库里残留旧路径 | 运行 `docker compose exec echopet-backend python -m backend.scripts.reindex_music --reset`。 |
| 音频文件损坏或格式不兼容 | 查看 `song_ingest_failures`，替换对应文件。 |

### 常见日志

| 日志 | 含义 |
| --- | --- |
| `QFluentWidgets Pro is now released` | 第三方 UI 库提示，不是错误。 |
| `qt.qpa.fonts: DirectWrite...` | Windows 字体加载警告，通常不影响使用。 |
| `qt.multimedia.ffmpeg...` | Qt 多媒体模块提示，不是错误。 |
| `Could not load dynamic library 'libcuda...'` | TensorFlow 提示没有 GPU，CPU 可以继续跑。 |

## 项目结构

```text
echopet/
├── backend/
│   ├── api/                    # FastAPI routes
│   ├── models/                 # SQLAlchemy models and local ML model files
│   ├── music/                  # 本地曲库
│   ├── scripts/                # 模型下载和曲库重建脚本
│   ├── services/               # 核心业务逻辑
│   └── tests/                  # 后端测试
├── DyberPet-main/
│   ├── DyberPet/               # DyberPet 桌宠代码
│   ├── frontend/               # EchoPet 面板、API client、录音、快捷键
│   └── run_DyberPet.py         # 前端入口
├── docs/
│   └── design_system.md        # UI 方向和视觉规范
├── scripts/
│   ├── start_backend.ps1       # 本地后端启动脚本
│   ├── start_echopet.ps1       # 一键启动脚本
│   └── stop_echopet.ps1        # 停止前后端
├── api_docs.md                 # API 文档
├── product_design.md           # 产品概念和 MVP 范围
├── docker-compose.yml
└── README.md
```

## Roadmap

当前 MVP：

- 桌宠入口
- 文本与语音输入
- 基于上下文的音乐推荐
- 本地曲库入库
- 真实音频特征和 embedding
- 播放队列和隐式反馈
- 基础记忆与用户画像更新

后续方向：

- 更完整的状态专属桌宠动画
- 更自然的推荐解释
- 更明确的上下文隐私控制
- 更稳定的播放队列连续性和会话恢复
- 可导出的用户偏好画像
- 更友好的 Windows 安装包

## License and Credits

EchoPet 基于 DyberPet 桌宠项目，并在其上连接了本地 FastAPI 推荐后端。打包或分发前，需要确认 DyberPet、第三方模型和音乐素材各自的 license 要求。
