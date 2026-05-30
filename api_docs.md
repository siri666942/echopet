# EchoPet API 接口文档

> Base URL: `http://localhost:8000`
>
> Content-Type: `application/json`
>
> 当前版本已对齐黑客松实现路线：`DyberPet` 作为前端基座，输入链路为 `录音 -> faster-whisper -> text -> analyze -> mpv`

---

## 目录

- [数据模型](#数据模型)
- [接口列表](#接口列表)
  - [1. POST /api/transcribe — 音频转文本](#1-post-apitranscribe)
  - [2. POST /api/analyze — 文本分析与推荐](#2-post-apianalyze)
  - [3. POST /api/feedback — 用户反馈](#3-post-apifeedback)
  - [4. GET /api/context — 获取环境上下文](#4-get-apicontext)
  - [5. GET /api/memory — 查询历史记忆](#5-get-apimemory)
  - [6. GET /api/player/status — 获取 mpv 播放状态](#6-get-apiplayerstatus)
  - [7. GET /api/music/random — 随机获取歌曲](#7-get-apimusicrandom)

---

## 数据模型

### Context（环境上下文）

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| hour | integer | 当前小时（0-23） | `2` |
| active_app | string | 当前活跃应用 | `"VSCode"` |
| kpm | integer | 每分钟按键次数 | `160` |
| backspace_ratio | float | 退格键占比（0-1） | `0.22` |

```json
{
  "hour": 2,
  "active_app": "VSCode",
  "kpm": 160,
  "backspace_ratio": 0.22
}
```

### Emotion（情绪分析结果）

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| emotion | string | 情绪标签 | `"frustrated"` |
| energy | float | 能量值（0-1） | `0.3` |
| need | string | 当前需求 | `"comfort"` |

可选 `emotion` 值：

`frustrated` / `sad` / `happy` / `focused` / `tired` / `anxious` / `calm`

可选 `need` 值：

`comfort` / `focus` / `energy` / `relaxation` / `companionship`

```json
{
  "emotion": "frustrated",
  "energy": 0.3,
  "need": "comfort"
}
```

### Song（歌曲）

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| id | string | 歌曲唯一ID | `"s001"` |
| title | string | 歌曲标题 | `"Midnight Rain"` |
| artist | string | 艺术家 | `"LoFi Dreams"` |
| tags | string[] | 标签列表 | `["lofi", "calm", "night"]` |
| energy | float | 能量值（0-1） | `0.3` |
| mood | string | 情绪标签 | `"soothing"` |
| file_path | string | 本地文件路径，供 `mpv` 播放 | `"C:/music/s001.mp3"` |

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

### MemoryEntry（记忆条目）

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| timestamp | datetime | ISO 8601 时间戳 | `"2025-01-15T02:30:00"` |
| context | Context | 当时的环境上下文 | — |
| emotion | Emotion | 当时的情绪分析 | — |
| song_id | string | 推荐的歌曲ID | `"s001"` |
| feedback | string | 用户反馈 | `"positive"` |

```json
{
  "timestamp": "2025-01-15T02:30:00",
  "context": {
    "hour": 2,
    "active_app": "VSCode",
    "kpm": 160,
    "backspace_ratio": 0.22
  },
  "emotion": {
    "emotion": "frustrated",
    "energy": 0.3,
    "need": "comfort"
  },
  "song_id": "s001",
  "feedback": "positive"
}
```

### PlayerStatus（播放器状态）

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| player | string | 播放器名称 | `"mpv"` |
| status | string | 当前状态 | `"playing"` |
| track_id | string | 当前歌曲ID | `"s001"` |
| title | string | 当前歌曲名 | `"Midnight Rain"` |
| artist | string | 当前艺术家 | `"LoFi Dreams"` |

可选 `status` 值：

`idle` / `loading` / `playing` / `paused` / `error`

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

## 接口列表

### 1. `POST /api/transcribe`

> 录音入口接口。前端录音后，将音频提交给 `faster-whisper` 服务，返回识别文本。

**Request Body**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| audio | string | ✅ | 音频文件的 Base64 编码 |
| audio_format | string | ❌ | 音频格式，默认 `wav` |

```json
{
  "audio": "<base64 encoded audio>",
  "audio_format": "wav"
}
```

**Response `200 OK`**

```json
{
  "transcript": "我有点烦，来点适合现在的歌",
  "language": "zh",
  "source": "faster-whisper"
}
```

**错误响应**

| 状态码 | 说明 |
|--------|------|
| 400 | 缺少 audio 字段 |
| 422 | audio Base64 解码失败 |
| 500 | `faster-whisper` 服务异常 |

---

### 2. `POST /api/analyze`

> 核心接口。接收文本输入和环境上下文，返回情绪分析、桌宠状态、推荐歌曲和播放状态。

**Request Body**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | ✅ | 用户输入文本，可以来自直接输入，也可以来自 `faster-whisper` |
| input_source | string | ✅ | 输入来源，`text` 或 `faster_whisper` |
| context | Context | ✅ | 当前环境上下文 |

```json
{
  "text": "我有点烦，来点适合现在的歌",
  "input_source": "faster_whisper",
  "context": {
    "hour": 2,
    "active_app": "VSCode",
    "kpm": 160,
    "backspace_ratio": 0.22
  }
}
```

**Response `200 OK`**

| 字段 | 类型 | 说明 |
|------|------|------|
| transcript | string | 规范化后的文本，通常与输入一致 |
| emotion | Emotion | 情绪分析结果 |
| current_state | string | 前端可直接使用的桌宠状态 |
| bubble_text | string | 建议展示在桌宠气泡中的文案 |
| assistant_reply | string | 对用户的回复 |
| recommendation | Song | 推荐的歌曲 |
| play_action | string | 建议对 `mpv` 执行的动作 |
| player_status | string | 当前播放器状态 |

可选 `current_state` 值：

`idle` / `focus` / `tired` / `frustrated` / `sad`

可选 `play_action` 值：

`play` / `pause` / `skip` / `none`

```json
{
  "transcript": "我有点烦，来点适合现在的歌",
  "emotion": {
    "emotion": "frustrated",
    "energy": 0.3,
    "need": "comfort"
  },
  "current_state": "frustrated",
  "bubble_text": "你现在有点紧绷，我先放一点柔和的。",
  "assistant_reply": "我感觉你现在有点紧绷，先给你放一点舒缓但不太丧的。",
  "recommendation": {
    "id": "s001",
    "title": "Midnight Rain",
    "artist": "LoFi Dreams",
    "tags": ["lofi", "calm", "night"],
    "energy": 0.3,
    "mood": "soothing",
    "file_path": "C:/music/s001.mp3"
  },
  "play_action": "play",
  "player_status": "loading"
}
```

**错误响应**

| 状态码 | 说明 |
|--------|------|
| 400 | 缺少 text 或 context 字段 |
| 422 | 输入字段格式错误 |
| 500 | LLM、推荐器或播放器控制异常 |

---

### 3. `POST /api/feedback`

> 记录用户对推荐歌曲的反馈，用于更新记忆和后续推荐。

**Request Body**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| song_id | string | ✅ | 歌曲ID |
| feedback | string | ✅ | 反馈类型 |

可选 `feedback` 值：

| 值 | 含义 |
|----|------|
| `positive` | 喜欢 |
| `negative` | 不喜欢 |
| `too_quiet` | 太安静了 |
| `too_sad` | 太悲伤了 |
| `more_energy` | 想要更有力量 |

```json
{
  "song_id": "s001",
  "feedback": "positive"
}
```

**Response `200 OK`**

```json
{
  "status": "ok",
  "message": "Feedback recorded"
}
```

**错误响应**

| 状态码 | 说明 |
|--------|------|
| 400 | 缺少 song_id 或 feedback |
| 404 | song_id 不存在 |
| 422 | feedback 值不在允许范围内 |

---

### 4. `GET /api/context`

> 获取当前环境上下文信息。由后端环境感知模块实时采集。

**Request**

无请求参数。

**Response `200 OK`**

```json
{
  "hour": 2,
  "active_app": "VSCode",
  "kpm": 160,
  "backspace_ratio": 0.22
}
```

**错误响应**

| 状态码 | 说明 |
|--------|------|
| 500 | 环境感知模块异常 |

---

### 5. `GET /api/memory`

> 查询历史记忆条目，支持分页。

**Query Parameters**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | integer | ❌ | `20` | 每页条数 |
| offset | integer | ❌ | `0` | 偏移量 |

**请求示例**

```text
GET /api/memory?limit=10&offset=0
```

**Response `200 OK`**

```json
{
  "entries": [
    {
      "timestamp": "2025-01-15T02:30:00",
      "context": {
        "hour": 2,
        "active_app": "VSCode",
        "kpm": 160,
        "backspace_ratio": 0.22
      },
      "emotion": {
        "emotion": "frustrated",
        "energy": 0.3,
        "need": "comfort"
      },
      "song_id": "s001",
      "feedback": "positive"
    }
  ],
  "total": 42
}
```

---

### 6. `GET /api/player/status`

> 获取 `mpv` 当前播放状态，供前端轮询展示。

**Request**

无请求参数。

**Response `200 OK`**

```json
{
  "player": "mpv",
  "status": "playing",
  "track_id": "s001",
  "title": "Midnight Rain",
  "artist": "LoFi Dreams"
}
```

**错误响应**

| 状态码 | 说明 |
|--------|------|
| 500 | `mpv` 控制层异常 |

---

### 7. `GET /api/music/random`

> 从本地曲库中随机返回一首歌曲。

**Request**

无请求参数。

**Response `200 OK`**

```json
{
  "id": "s001",
  "title": "Midnight Rain",
  "artist": "LoFi Dreams",
  "file_path": "C:/music/s001.mp3"
}
```

**错误响应**

| 状态码 | 说明 |
|--------|------|
| 404 | 曲库为空 |

---

## 附录：推荐链路

```text
1. 前端录音
2. POST /api/transcribe
3. 得到 transcript
4. 前端请求 GET /api/context
5. POST /api/analyze(text + context)
6. 后端做记忆检索、LLM 编排、歌曲推荐
7. 后端控制 mpv 播放
8. 前端轮询 GET /api/player/status
9. 用户点击反馈后 POST /api/feedback
```

---

## 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-05-30 | v0.2 | 对齐 `DyberPet + faster-whisper + mpv` 黑客松架构，拆分 `transcribe` 与 `analyze`，补充播放器状态接口 |
