# EchoPet

EchoPet 是一个本地桌面情绪音乐 Agent。当前后端已经升级到架构 2.0：用户文本和上下文会先被翻译成“音乐检索语言”，再用真实 embedding 从本地曲库召回歌曲，生成播放队列，并通过播放完成率/跳过行为形成隐式反馈和长期用户画像。

## 当前能力

- FastAPI HTTP 接口服务
- SQLite 本地曲库、播放会话、记忆和用户画像
- 本地音乐扫描，自动提取音频特征
- 用歌曲描述生成真实 embedding，不使用假 embedding
- `/api/analyze` 返回 `session_id`、`retrieval_query`、`playlist`
- `/api/player/event` 接收播放完成率和跳过事件，更新歌曲统计
- 可选 mpv 播放控制；播放失败不会拖垮推荐接口

## 项目结构

```text
echopet/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── tests/
│   ├── db/
│   └── music/
├── api_docs.md
├── backend_dev_guide.md
├── product_design.md
└── techneque_design.md
```

## 环境要求

- Python 3.11+
- 真实 embedding API：必须配置 `OPENAI_API_KEY`
- 可选：`OPENAI_BASE_URL`，用于 StepFun、DeepSeek 等 OpenAI-compatible 服务
- 可选：安装 `mpv`
- 必须：安装 Essentia / Essentia TensorFlow 运行环境
- 可选：安装 FFmpeg，供音频解码链路使用

注意：推荐主链路不会生成假 embedding。没有 embedding 配置时，服务能启动，但 `/api/analyze` 会返回明确错误，提示需要配置真实 embedding API。

## 安装和启动

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/pip install -r backend/requirements.txt
backend/.venv/Scripts/python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

打开：

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

## 环境变量

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small

WHISPER_MODEL=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8

ESSENTIA_GENRE_MODEL_PATH=
ESSENTIA_MOOD_MODEL_PATH=
ESSENTIA_DANCEABILITY_MODEL_PATH=
ESSENTIA_AROUSAL_VALENCE_MODEL_PATH=
ESSENTIA_VOICE_INSTRUMENTAL_MODEL_PATH=
ESSENTIA_ACOUSTIC_ELECTRONIC_MODEL_PATH=

ENABLE_MPV=true
MPV_BINARY=mpv

DATABASE_URL=sqlite:///backend/db/echopet.db
MUSIC_DIR=backend/music
HOST=127.0.0.1
PORT=8000
```

## 接口概览

| 方法 | 路径 | 说明 |
|---|---|---|
| `POST` | `/api/transcribe` | Base64 音频转文本 |
| `POST` | `/api/analyze` | 文本 + 上下文 -> retrieval_query + playlist + 播放 |
| `POST` | `/api/player/event` | 上报 finished/skipped/stopped 等播放事件 |
| `GET` | `/api/context` | 获取当前桌面上下文 |
| `GET` | `/api/memory` | 分页查询兼容记忆 |
| `GET` | `/api/player/status` | 获取当前 mpv 播放状态 |
| `GET` | `/api/music/random` | 调试用：随机取一首歌 |

## 曲库流程

把 `.mp3`、`.wav` 或 `.flac` 放到 `backend/music/` 后，服务启动时会：

1. 扫描新歌
2. 用 Essentia / Essentia TensorFlow 模型提取基础音频特征和高级语义特征
3. 生成只描述歌曲本身的中文 description
4. 调用真实 embedding API
5. 写入 songs 表

旧歌曲缺少 `audio_features`、`description`、`embedding` 时，也会在启动时自动补全。Essentia 分析失败的新歌不会写入 songs 表，会记录为入库失败；如果没有配置 embedding API，则不会写假向量。

## 前端联调流程

```text
用户输入文本或录音
  -> 如果是录音，先 POST /api/transcribe
  -> GET /api/context
  -> POST /api/analyze
  -> 前端使用 current_state / bubble_text / playlist / session_id
  -> 前端轮询 GET /api/player/status
  -> 播放结束或跳过时 POST /api/player/event
```

## 测试

```powershell
python -m pytest backend/tests
```

当前测试覆盖 embedding 相似度、歌曲描述、playlist、画像反思、embedding 推荐器、`/api/analyze`、`/api/player/event`、曲库随机接口、上下文接口、记忆分页和语音转写校验。
