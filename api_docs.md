# EchoPet API 接口文档

> Base URL: `http://localhost:8000`
>
> Content-Type: `application/json`
>
> 当前后端主链路是 2.0 架构：用户文本和上下文进入 `/api/analyze`，后端生成音乐检索语句，使用真实 embedding 召回歌曲，返回播放队列，并用 `/api/player/event` 接收播放完成率或跳过事件。

## 数据模型

### Context

环境上下文由后端和前端共同组成。当前 MVP 中键盘指标可以为 0。

```json
{
  "hour": 22,
  "active_app": "VSCode",
  "kpm": 0,
  "backspace_ratio": 0.0
}
```

字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `hour` | integer | 当前小时，范围 0-23 |
| `active_app` | string | 当前活跃应用 |
| `kpm` | integer | 每分钟按键数 |
| `backspace_ratio` | float | 退格比例，范围 0-1 |

### Emotion

这是兼容旧前端的字段。新版推荐不靠它做主排序，真正推荐依据是 `retrieval_query` 和歌曲 embedding。

```json
{
  "emotion": "focused",
  "energy": 0.55,
  "need": "focus"
}
```

### Song

接口会返回歌曲元数据、Essentia 音频特征和播放统计，但不会返回 embedding 原始向量。

```json
{
  "id": "song-001",
  "title": "示例歌曲",
  "artist": "本地曲库",
  "tags": ["essentia"],
  "energy": 0.62,
  "mood": "calm",
  "file_path": "backend/music/example.mp3",
  "description": "中速、响度适中、节奏稳定的器乐片段。",
  "audio_features": {
    "basic": {
      "duration": 185.2,
      "bpm": 92.0,
      "loudness": -14.1,
      "dynamic_complexity": 3.4,
      "spectral_centroid": 2100.0,
      "spectral_energy": 0.82,
      "danceability": 0.48,
      "key": "C",
      "scale": "minor"
    }
  },
  "semantic_features": {
    "genre": {},
    "mood": {},
    "arousal": null,
    "valence": null,
    "voice_instrumental": {}
  },
  "play_count": 3,
  "avg_completion_rate": 0.74
}
```

### PlayerStatus

```json
{
  "player": "mpv",
  "status": "playing",
  "track_id": "song-001",
  "title": "示例歌曲",
  "artist": "本地曲库"
}
```

`status` 可选值：`idle`、`loading`、`playing`、`paused`、`error`。

## 接口列表

### POST `/api/transcribe`

把前端录音的 base64 音频转成文字。

请求：

```json
{
  "audio": "<base64 encoded audio>",
  "audio_format": "wav"
}
```

响应：

```json
{
  "transcript": "我现在想进入专注状态",
  "language": "zh",
  "source": "faster-whisper"
}
```

常见错误：

| 状态码 | 说明 |
| --- | --- |
| 400/422 | audio 缺失或不是合法 base64 |
| 500 | 语音识别服务异常 |

### POST `/api/analyze`

核心推荐接口。前端提交文本和上下文，后端返回桌宠状态、气泡文案、第一首推荐歌、完整 playlist 和本次播放会话 `session_id`。

请求：

```json
{
  "text": "我现在有点累，但还想继续写代码",
  "input_source": "text",
  "context": {
    "hour": 22,
    "active_app": "VSCode",
    "kpm": 0,
    "backspace_ratio": 0.0
  }
}
```

响应：

```json
{
  "transcript": "我现在有点累，但还想继续写代码",
  "emotion": {
    "emotion": "tired",
    "energy": 0.3,
    "need": "focus"
  },
  "current_state": "tired",
  "bubble_text": "我给你找一点不吵、能托住注意力的歌。",
  "assistant_reply": "先放一首节奏稳定但不刺激的，让你慢慢续上。",
  "recommendation": {
    "id": "song-001",
    "title": "示例歌曲",
    "artist": "本地曲库",
    "tags": ["essentia"],
    "energy": 0.62,
    "mood": "calm",
    "file_path": "backend/music/example.mp3",
    "description": "中速、响度适中、节奏稳定的器乐片段。",
    "audio_features": {},
    "semantic_features": {},
    "play_count": 3,
    "avg_completion_rate": 0.74
  },
  "play_action": "play",
  "player_status": "playing",
  "session_id": "a1b2c3",
  "retrieval_query": "中低能量、节奏稳定、干扰少、适合持续专注的音乐",
  "playlist": []
}
```

说明：

| 字段 | 说明 |
| --- | --- |
| `session_id` | 本次播放会话 ID，前端上报播放事件时必须带上 |
| `retrieval_query` | LLM 生成的音乐检索语言 |
| `playlist` | Top 5 推荐队列，第一首通常等于 `recommendation` |
| `emotion` | 兼容字段，不是新版推荐主依据 |

常见错误：

| 状态码 | 说明 |
| --- | --- |
| 422 | 请求字段格式错误 |
| 503 | 没有可用歌曲、歌曲缺少 embedding、或 embedding API 未配置 |
| 500 | LLM、播放器或数据库异常 |

### POST `/api/player/event`

隐式反馈接口。前端不要再调用旧的显式反馈接口。播放结束、跳过或停止时，把完成率交给后端，用于更新 PlaySession、歌曲统计和用户画像。

请求：

```json
{
  "session_id": "a1b2c3",
  "event": "ended",
  "completion_rate": 0.9,
  "ended_reason": "finished"
}
```

字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | string | `/api/analyze` 返回的会话 ID |
| `event` | string | 当前固定传 `ended` 即可 |
| `completion_rate` | float | 完成率，范围 0-1 |
| `ended_reason` | string | `finished`、`skipped`、`stopped`、`unknown` |

响应：

```json
{
  "status": "ok",
  "message": "Player event recorded"
}
```

常见错误：

| 状态码 | 说明 |
| --- | --- |
| 404 | `session_id` 不存在 |
| 422 | 完成率或结束原因格式错误 |

### GET `/api/context`

获取当前环境上下文。

响应：

```json
{
  "hour": 22,
  "active_app": "VSCode",
  "kpm": 0,
  "backspace_ratio": 0.0
}
```

### GET `/api/memory`

分页查询旧版记忆条目，主要用于调试。

请求示例：

```text
GET /api/memory?limit=20&offset=0
```

响应：

```json
{
  "entries": [],
  "total": 0
}
```

### GET `/api/player/status`

查询 mpv 播放状态，前端可以轮询。

响应：

```json
{
  "player": "mpv",
  "status": "idle",
  "track_id": null,
  "title": null,
  "artist": null
}
```

### GET `/api/music/random`

调试接口：从曲库中随机返回一首歌。不参与新版推荐主链路。

响应：

```json
{
  "id": "song-001",
  "title": "示例歌曲",
  "artist": "本地曲库",
  "tags": ["essentia"],
  "energy": 0.62,
  "mood": "calm",
  "file_path": "backend/music/example.mp3",
  "description": "中速、响度适中、节奏稳定的器乐片段。",
  "audio_features": {},
  "semantic_features": {},
  "play_count": 3,
  "avg_completion_rate": 0.74
}
```

如果曲库为空，返回 404。

## 前端联调约定

前端目录保持为 `DyberPet-main/frontend/`。运行 DyberPet 时，`DyberPet-main` 是 Python 导入根目录，所以代码里继续使用 `from frontend...`。

推荐交互流程：

```text
1. 前端获取上下文：GET /api/context
2. 前端提交文本：POST /api/analyze
3. 前端保存响应里的 session_id
4. 前端展示 current_state、bubble_text、recommendation、playlist
5. 播放结束或用户点击 KEEP：POST /api/player/event，completion_rate=0.9，ended_reason=finished
6. 用户点击 SKIP：POST /api/player/event，completion_rate=0.1，ended_reason=skipped
```

## 变更记录

| 日期 | 版本 | 说明 |
| --- | --- | --- |
| 2026-05-31 | v2.0 | 删除旧显式反馈文档，改为 embedding 推荐、playlist 和 `/api/player/event` 隐式反馈 |
