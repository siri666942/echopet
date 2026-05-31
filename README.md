# EchoPet 本地运行说明

EchoPet 是一个桌面音乐 Agent：前端是 DyberPet 桌宠，后端是 FastAPI。当前唯一推荐运行方式是：

```text
后端：Docker 跑 Linux 环境，负责 Essentia、embedding、曲库、API
前端：Windows 本地 Python venv 跑 DyberPet 桌宠
```

不要再用 Windows 本地 venv 跑后端主链路。原因很简单：真实歌曲入库需要 `essentia-tensorflow`，这个包在 Windows + Python 3.11 下没有合适的 PyPI wheel，本地直接装会失败。Docker 里的 Linux 环境已经验证能安装并 import Essentia。

## 目录结构

```text
echopet/
├── backend/                  # FastAPI 后端
│   ├── Dockerfile             # 后端 Docker 镜像
│   ├── requirements.txt       # 后端基础依赖
│   ├── requirements-essentia.txt
│   ├── music/                 # 你的本地音乐放这里
│   └── db/                    # SQLite 数据库
├── DyberPet-main/             # 桌宠前端
│   ├── requirements.txt       # 前端依赖
│   └── run_DyberPet.py        # 前端启动入口
├── docker-compose.yml
├── api_docs.md
└── README.md
```

## 第一次启动后端

先确认 Docker Desktop 已经打开。

在项目根目录运行：

```powershell
docker compose up -d --build
```

这个命令会做三件事：

1. 构建后端镜像。
2. 安装后端依赖和 `essentia-tensorflow`。
3. 启动后端服务到 `http://127.0.0.1:8000`。

确认后端活着：

```powershell
Invoke-WebRequest http://127.0.0.1:8000/
```

能看到类似下面的返回就说明后端启动成功：

```json
{"service":"EchoPet API","version":"0.2.0"}
```

Swagger 页面：

```text
http://127.0.0.1:8000/docs
```

## 准备真实模型

后端现在不写假特征，也不写假向量。真实歌曲入库需要两类模型：

1. Essentia TensorFlow 音频模型：分析歌曲本身的节奏、响度、调性、情绪、风格等。
2. 本地中文 embedding 模型：把歌曲描述和用户需求变成向量，用来做语义召回。

第一次跑项目时执行：

```powershell
python -m backend.scripts.download_essentia_models
docker compose exec echopet-backend python -c "from backend.services.embedding_service import embed_text; print(len(embed_text('测试中文向量')))"
```

第一条命令会把 Essentia 官方模型下载到：

```text
backend/models/essentia/
```

第二条命令会准备本地中文向量模型，正常会输出：

```text
512
```

这些模型文件很大，不提交 git，但会留在你的本地 `backend/models/` 里。以后除非你删了这个目录，否则不用重复准备。

## 一键启动/停止

推荐直接用脚本，不用一条条输命令。

一键启动前后端：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_echopet.ps1
```

这个脚本会自动做这些事：

1. 启动 Docker 后端。
2. 等待 `http://127.0.0.1:8000` 可用。
3. 检查 `backend/music/` 里的 `.mp3/.wav/.flac` 是否有变化。
4. 如果曲库有变化，自动执行 `backend.scripts.reindex_music`；没有变化就跳过。
5. 检查并启动前端桌宠。

如果改了后端代码、Dockerfile 或依赖，需要重新构建镜像：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_echopet.ps1 -Build
```

如果想强制重扫曲库：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_echopet.ps1 -ForceReindex
```

如果第一次跑前端或依赖变了：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_echopet.ps1 -InstallFrontendDeps
```

一键停止前后端：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/stop_echopet.ps1
```

它会停止脚本启动的前端进程，并停止 Docker 后端容器。

## 手动启动后端

以后如果代码没改，只需要：

```powershell
docker compose up -d
```

如果改了后端代码、Dockerfile 或依赖：

```powershell
docker compose up -d --build
```

看后端是否正在运行：

```powershell
docker compose ps
```

## 手动停止后端

临时停止：

```powershell
docker compose stop
```

重新启动：

```powershell
docker compose start
```

停止并删除容器：

```powershell
docker compose down
```

`down` 不会删除 `backend/db/` 和 `backend/music/`，因为它们是本地文件夹。

## 查看后端日志

实时看日志：

```powershell
docker compose logs -f echopet-backend
```

只看最近 100 行：

```powershell
docker compose logs --tail 100 echopet-backend
```

退出实时日志：按 `Ctrl + C`。这只会退出看日志，不会停止后端。

## 端口被占用

后端需要占用 `8000` 端口。如果启动失败，先查谁占了端口：

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

如果看到某个旧 Python 进程占着，可以按进程号停止，例如：

```powershell
Stop-Process -Id 48912 -Force
```

然后重新启动 Docker 后端：

```powershell
docker compose up -d
```

## 前端安装

前端只需要 Windows 本地跑，不进 Docker。

在项目根目录运行：

```powershell
python -m venv DyberPet-main/.venv
DyberPet-main/.venv/Scripts/pip install -r DyberPet-main/requirements.txt
```

前端依赖一共这些：

```text
PySide6
PySide6-Fluent-Widgets
PySideSix-Frameless-Window
APScheduler
pynput
tendo
```

注意：代码里 import 叫 `qfluentwidgets`，但 pip 包名是 `PySide6-Fluent-Widgets`。

## 启动前端

必须先进入 `DyberPet-main` 目录：

```powershell
cd DyberPet-main
.venv/Scripts/python run_DyberPet.py
```

不要在项目根目录直接这样跑：

```powershell
DyberPet-main/.venv/Scripts/python DyberPet-main/run_DyberPet.py
```

这样会让 DyberPet 找不到 `res/language/language.json` 这类资源文件。

## 前端怎么用

1. 先启动后端：`docker compose up -d`
2. 再启动前端：`cd DyberPet-main`，然后 `.venv/Scripts/python run_DyberPet.py`
3. 桌面上会出现桌宠。
4. 用鼠标右键点桌宠。
5. 点菜单里的 `[ OPEN ECHOPET ]`。
6. 弹出的 EchoPet 面板里输入一句话。
7. 点 `[ SUBMIT ]`。
8. 如果要录音，点红色圆形 `REC`，录完后确认文本再提交。
9. 推荐出来后：
   - `[ KEEP ]`：告诉后端这次播放完成率高。
   - `[ SKIP ]`：告诉后端这首被跳过。
   - `[ BOOST ]`：当前禁用，因为后端没有对应接口。

当前没有全局快捷键。打开 EchoPet 面板靠右键桌宠菜单。

## 前后端怎么接起来

前端请求都在：

```text
DyberPet-main/frontend/agent_client.py
```

主流程：

```text
输入文字或录音
  -> GET /api/context
  -> POST /api/analyze
  -> 后端返回 current_state、bubble_text、recommendation、session_id、playlist
  -> 前端显示气泡和歌曲
  -> 前端轮询 GET /api/player/status
  -> KEEP/SKIP 时 POST /api/player/event
```

关键文件：

```text
DyberPet-main/DyberPet/DyberPet.py      # 把桌宠、输入面板、HTTP 客户端接起来
DyberPet-main/frontend/input_panel.py   # EchoPet 输入面板
DyberPet-main/frontend/state_mapper.py  # 后端响应转前端状态
backend/api/analyze.py                  # 推荐主接口
backend/services/music_service.py       # 曲库扫描和入库
backend/scripts/reindex_music.py        # 手动重扫曲库
```

## 放音乐

把音乐文件放到：

```text
backend/music/
```

支持：

```text
.mp3
.wav
.flac
```

放完新歌后，让后端重新扫描：

```powershell
docker compose exec echopet-backend python -m backend.scripts.reindex_music
```

如果你想清空旧曲库记录，完全按当前 `backend/music/` 重建：

```powershell
docker compose exec echopet-backend python -m backend.scripts.reindex_music --reset
```

当前我已经跑通过一次，结果是：

```text
songs=22
failures=0
```

如果你以后又放了新歌，看到 `failures=0` 才表示所有新歌都成功入库。只要有失败，就说明那首歌没有被写进推荐库。

看当前入库结果：

```powershell
docker compose exec echopet-backend python -c "from backend.models.database import SessionLocal; from backend.models.tables import Song, SongIngestFailure; db=SessionLocal(); print('songs=', db.query(Song).count()); print('failures=', db.query(SongIngestFailure).count()); db.close()"
```

## 曲库为什么可能失败

后端现在要求真实音频分析和真实向量，不允许写假数据。失败一般只有三类：

第一类：模型没准备好。先跑：

```powershell
python -m backend.scripts.download_essentia_models
docker compose exec echopet-backend python -c "from backend.services.embedding_service import embed_text; print(len(embed_text('测试中文向量')))"
```

第二类：数据库里残留了旧路径。如果看到：

```text
file not found during backfill
```

而路径是 Windows 绝对路径，说明数据库里残留了以前本地运行后端时写进去的旧记录。直接重建曲库：

```powershell
docker compose exec echopet-backend python -m backend.scripts.reindex_music --reset
```

第三类：音频文件本身坏了，或者 Essentia 读不了这个格式。这个文件会记到 `song_ingest_failures`，不会进入推荐库。

## 环境变量

项目根目录 `.env` 主要放聊天大模型配置：

```env
OPENAI_API_KEY=你的 key
OPENAI_BASE_URL=https://api.stepfun.com/v1
OPENAI_MODEL=step-3.7-flash
```

当前 embedding 默认走本地真实模型：

```env
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

如果你以后有支持 `/v1/embeddings` 的 OpenAI 兼容服务，再改成：

```env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=服务商给你的 embedding 模型名
```

注意：StepFun 当前聊天模型能用，但它的模型列表里没有 embedding 模型，所以项目默认不用 StepFun 做 embedding。

## 常见日志

```text
QFluentWidgets Pro is now released
```

第三方 UI 库广告提示，不是错误。

```text
qt.qpa.fonts: DirectWrite: CreateFontFaceFromHDC() failed ... Courier ...
```

Windows 字体加载警告。Qt 会自动换字体，通常不影响使用。

```text
qt.multimedia.ffmpeg: Using Qt multimedia with FFmpeg ...
```

Qt 多媒体模块提示正在使用 FFmpeg，不是错误。

```text
Could not load dynamic library 'libcuda...'
```

Docker 里的 TensorFlow 在提示没有 GPU/CUDA。CPU 可以继续跑，不是阻塞错误。

```text
RuntimeError: libshiboken: Internal C++ object ... already deleted
```

这是前端状态条对象被 Qt 销毁后，定时器还尝试更新它。当前代码已经加了对象有效性检查，后续不应该再因为这个崩。

## 测试

后端测试：

```powershell
docker compose exec echopet-backend python -m pytest backend/tests
```

前端语法检查：

```powershell
DyberPet-main/.venv/Scripts/python -m compileall DyberPet-main/frontend DyberPet-main/DyberPet/DyberPet.py
```
