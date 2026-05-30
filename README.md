# EchoPet

EchoPet 是一个本地桌面情绪音乐 Agent。它接收用户输入，读取轻量桌面上下文，分析用户当前状态，从本地曲库推荐音乐，并通过 `mpv` 控制播放。

当前项目优先完成后端 MVP：

- FastAPI HTTP 接口服务
- SQLite 本地记忆和曲库元数据
- 本地曲库扫描
- 可选 OpenAI 情绪分析；没有 Key 时使用规则兜底
- 可选 faster-whisper 语音转写；不可用时不影响服务启动
- 可选 mpv 播放控制；不可用时仍返回可观察的播放器状态

## 项目结构

```text
echopet/
├── backend/
│   ├── main.py              # FastAPI 应用入口
│   ├── config.py            # 环境变量和默认配置
│   ├── requirements.txt     # 后端 Python 依赖
│   ├── api/                 # HTTP 路由
│   ├── models/              # SQLAlchemy 表和 Pydantic 模型
│   ├── services/            # 业务逻辑
│   ├── tests/               # Pytest 测试
│   ├── db/                  # 运行时 SQLite 数据库，不提交 git
│   └── music/               # 本地音乐文件目录
├── api_docs.md              # API 接口文档
├── backend_guide.md         # 后端设计指南
├── backend_dev_guide.md     # 后端开发说明
├── product_design.md        # 产品设计
└── techneque_design.md      # 技术架构文档
```

## 环境要求

- Python 3.11+
- 可选：安装 `mpv`，并确保命令行里能访问
- 可选：安装 FFmpeg，用于真实音频转写流程
- 可选：配置 `OPENAI_API_KEY`，用于 LLM 情绪分析

后端即使没有 OpenAI、faster-whisper 或 mpv，也会继续运行。这样前端可以先联调接口，不会被外部依赖卡住。

## 后端启动

在项目根目录执行：

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/pip install -r backend/requirements.txt
```

启动 API 服务：

```powershell
backend/.venv/Scripts/python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

打开：

- 服务根路径：`http://127.0.0.1:8000/`
- Swagger 接口文档：`http://127.0.0.1:8000/docs`

## 环境变量

如果需要覆盖默认配置，在项目根目录创建 `.env`：

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

WHISPER_MODEL=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8

ENABLE_MPV=true
MPV_BINARY=mpv

DATABASE_URL=sqlite:///backend/db/echopet.db
MUSIC_DIR=backend/music
HOST=127.0.0.1
PORT=8000
```

注意：

- 不要提交 `.env`，它已经被 `.gitignore` 忽略。
- `backend/db/*.db` 是运行时数据库，不提交 git。
- 本地音乐放到 `backend/music/`，支持 `.mp3`、`.wav`、`.flac`。
- 如果曲库为空，后端会自动插入 3 条样例歌曲元数据，保证演示接口能跑通。

## 接口概览

基础地址：`http://127.0.0.1:8000`

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/transcribe` | Base64 音频转文本 |
| `POST` | `/api/analyze` | 文本 + 上下文 -> 情绪、推荐、播放 |
| `POST` | `/api/feedback` | 记录用户对歌曲的反馈 |
| `GET` | `/api/context` | 获取当前桌面上下文 |
| `GET` | `/api/memory` | 分页查询历史记忆 |
| `GET` | `/api/player/status` | 获取当前 mpv 播放状态 |
| `GET` | `/api/music/random` | 从本地曲库随机取一首歌 |

完整请求和响应格式见 `api_docs.md`。

## 快速验证

启动 API 后，可以用 PowerShell 试一下：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/context
Invoke-RestMethod http://127.0.0.1:8000/api/music/random
```

测试文本分析：

```powershell
$body = @{
  text = "我 debug 一天了，有点烦"
  input_source = "text"
  context = @{
    hour = 23
    active_app = "VSCode"
    kpm = 120
    backspace_ratio = 0.2
  }
} | ConvertTo-Json -Depth 4

Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/api/analyze `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

## 测试

在项目根目录执行：

```powershell
python -m pytest backend/tests
```

当前测试覆盖：

- `/api/context` 返回合法上下文
- `/api/music/random` 在样例曲库下能返回歌曲
- `/api/analyze` 在无 OpenAI、无 mpv 环境下仍能返回推荐并写入记忆
- `/api/feedback` 成功、未知歌曲、非法反馈
- `/api/memory` 分页查询
- `/api/player/status` 默认播放器状态
- `/api/transcribe` 请求校验

## 前端联调流程

DyberPet 前端建议按这个链路接入：

```text
用户输入文本或录音
  -> 如果是录音，先 POST /api/transcribe
  -> GET /api/context
  -> POST /api/analyze
  -> 前端根据 current_state 切桌宠状态
  -> 前端显示 bubble_text
  -> 前端轮询 GET /api/player/status
  -> 用户反馈时 POST /api/feedback
```

后端负责记忆、推荐、情绪分析、语音转写和播放控制。前端负责录音、桌宠动画、气泡展示和反馈按钮。
