# EchoPet 技术设计文档

---

# 技术架构

> 对齐黑客松实现路线：`DyberPet` 作为前端桌宠基座，输入链路为 `录音 → faster-whisper → text → analyze → mpv`

                ┌──────────────┐
                │   Frontend   │
                │   DyberPet   │
                └──────┬───────┘
                       │
                  HTTP API
                       │
                ┌──────▼───────┐
                │   Backend    │
                │    Agent     │
                └──────┬───────┘
                       │
     ┌─────────────────┼──────────────────┐
     │                 │                  │
     ▼                 ▼                  ▼

 Environment       Memory          Music Library
     │                                    │
     └──────────────┬─────────────────────┘
                    ▼
               mpv Player

---

# 技术栈

## Frontend

桌宠基座：

- DyberPet（桌面宠物框架）

---

## Backend

- Python 3.11+
- FastAPI

---

## Database

- SQLite

---

## AI能力

- faster-whisper（语音转文字，本地部署）
- GPT / Claude（情绪分析）

---

## 播放器

- mpv（音乐播放，后端通过 IPC 控制）

---

# 模块划分

## Frontend（DyberPet）

负责：

- 桌宠UI与动画
- 录音
- 状态展示（气泡文案、桌宠状态切换）
- 用户反馈
- 键盘节奏采集（kpm、backspace_ratio），通过 context 传给后端

不负责：

- 音乐播放（由后端控制 mpv）
- Memory
- 推荐算法
- 环境感知（时间、当前应用由后端采集）

---

## Backend

负责：

- faster-whisper 调用
- LLM 调用
- 环境感知（时间、当前应用；键盘数据由前端传入）
- Memory
- 推荐器
- 曲库管理
- mpv 播放器控制

---

# 数据流

1. 前端录音

2. POST /api/transcribe → faster-whisper → 得到 transcript

3. 前端采集 kpm / backspace_ratio

4. 前端请求 GET /api/context?kpm=xx&backspace_ratio=xx → 获取完整环境上下文

5. POST /api/analyze(text + context) → 后端做 Memory 检索、LLM 情绪分析、歌曲推荐

6. 后端控制 mpv 播放推荐歌曲

7. 前端轮询 GET /api/player/status → 同步播放状态

8. 用户反馈 POST /api/feedback → Memory 更新

---

# 数据模型

> 完整请求/响应模型见 [api_docs.md](api_docs.md)

## Context

```json
{
  "hour": 2,
  "active_app": "VSCode",
  "kpm": 160,
  "backspace_ratio": 0.22
}
```

## Emotion

```json
{
  "emotion": "frustrated",
  "energy": 0.3,
  "need": "comfort"
}
```

## Song

```json
{
  "id": "s001",
  "title": "Midnight Rain",
  "artist": "LoFi Dreams",
  "tags": ["lofi", "calm", "night"],
  "energy": 0.3,
  "mood": "soothing",
  "file_path": "C:/music/s001.mp3"
}
```

## MemoryEntry

```json
{
  "timestamp": "2025-01-15T02:30:00",
  "context": { "hour": 2, "active_app": "VSCode", "kpm": 160 },
  "emotion": { "emotion": "frustrated", "energy": 0.3 },
  "song_id": "s001",
  "feedback": "positive"
}
```

## PlayerStatus

```json
{
  "player": "mpv",
  "status": "playing",
  "track_id": "s001",
  "title": "Midnight Rain",
  "artist": "LoFi Dreams"
}
```

---

# API 接口

> 完整接口文档见 [api_docs.md](api_docs.md)

| #  | 方法 | 路由               | 说明                              |
| -- | ---- | ------------------ | --------------------------------- |
| 1 | POST | `/api/transcribe` | 音频转文本（faster-whisper） |
| 2 | POST | `/api/analyze` | 文本分析 + 情绪识别 + 歌曲推荐 + 控制 mpv |
| 3 | POST | `/api/feedback` | 用户反馈 |
| 4 | GET | `/api/context` | 获取环境上下文 |
| 5 | GET | `/api/memory` | 查询历史记忆（分页） |
| 6 | GET | `/api/player/status` | 获取 mpv 播放状态 |
| 7 | GET | `/api/music/random` | 随机获取歌曲 |

---

# 存储设计

## SQLite 表

### songs

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT PK | 歌曲ID |
| title | TEXT | 标题 |
| artist | TEXT | 艺术家 |
| tags | TEXT | 标签（JSON数组） |
| energy | REAL | 能量值 0-1 |
| mood | TEXT | 情绪标签 |
| file_path | TEXT | 绝对路径，供 mpv 播放 |

### memory

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | 自增ID |
| timestamp | DATETIME | 时间戳 |
| hour | INTEGER | 小时 |
| active_app | TEXT | 当前应用 |
| kpm | INTEGER | 按键频率 |
| backspace_ratio | REAL | 退格比例 |
| emotion | TEXT | 情绪 |
| energy | REAL | 能量值 |
| song_id | TEXT FK | 歌曲ID |
| feedback | TEXT | 用户反馈 |

---

# 推荐算法（简版）

1. 获取当前 context
2. 从 memory 中检索相似场景（相近 hour + 相同 active_app）
3. 统计这些场景下 feedback 为 positive 的歌曲
4. 按 energy 匹配当前 emotion 的 energy
5. 返回匹配度最高的歌曲