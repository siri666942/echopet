# EchoPet API 接口文档

> Base URL: `http://localhost:8000`
>
> Content-Type: `application/json`（除音频上传外）

---

## 目录

- [数据模型](#数据模型)
- [接口列表](#接口列表)
  - [1. POST /api/analyze — 情绪分析与音乐推荐](#1-post-apianalyze)
  - [2. POST /api/feedback — 用户反馈](#2-post-apifeedback)
  - [3. GET /api/context — 获取环境上下文](#3-get-apicontext)
  - [4. GET /api/memory — 查询历史记忆](#4-get-apimemory)
  - [5. GET /api/music/random — 随机获取歌曲](#5-get-apimusicrandom)

---

## 数据模型

### Context（环境上下文）


| 字段              | 类型      | 说明         | 示例         |
| --------------- | ------- | ---------- | ---------- |
| hour            | integer | 当前小时（0-23） | `2`        |
| active_app      | string  | 当前活跃应用     | `"VSCode"` |
| kpm             | integer | 每分钟按键次数    | `160`      |
| backspace_ratio | float   | 退格键占比（0-1） | `0.22`     |


```json
{
  "hour": 2,
  "active_app": "VSCode",
  "kpm": 160,
  "backspace_ratio": 0.22
}
```

### Emotion（情绪分析结果）


| 字段      | 类型     | 说明                 | 示例             |
| ------- | ------ | ------------------ | -------------- |
| emotion | string | 情绪标签               | `"frustrated"` |
| energy  | float  | 能量值（0-1），0=低落，1=亢奋 | `0.3`          |
| need    | string | 当前需求               | `"comfort"`    |


可选 emotion 值：`frustrated` / `sad` / `happy` / `focused` / `tired` / `anxious` / `calm`

可选 need 值：`comfort` / `focus` / `energy` / `relaxation` / `companionship`

```json
{
  "emotion": "frustrated",
  "energy": 0.3,
  "need": "comfort"
}
```

### Song（歌曲）


| 字段        | 类型       | 说明       | 示例                          |
| --------- | -------- | -------- | --------------------------- |
| id        | string   | 歌曲唯一ID   | `"s001"`                    |
| title     | string   | 歌曲标题     | `"Midnight Rain"`           |
| artist    | string   | 艺术家      | `"LoFi Dreams"`             |
| tags      | string[] | 标签列表     | `["lofi", "calm", "night"]` |
| energy    | float    | 能量值（0-1） | `0.3`                       |
| mood      | string   | 情绪标签     | `"soothing"`                |
| file_path | string   | 文件路径     | `"/music/s001.mp3"`         |


```json
{
  "id": "s001",
  "title": "Midnight Rain",
  "artist": "LoFi Dreams",
  "tags": ["lofi", "calm", "night"],
  "energy": 0.3,
  "mood": "soothing",
  "file_path": "/music/s001.mp3"
}
```

### MemoryEntry（记忆条目）


| 字段        | 类型       | 说明           | 示例                      |
| --------- | -------- | ------------ | ----------------------- |
| timestamp | datetime | ISO 8601 时间戳 | `"2025-01-15T02:30:00"` |
| context   | Context  | 当时的环境上下文     | —                       |
| emotion   | Emotion  | 当时的情绪分析      | —                       |
| song_id   | string   | 推荐的歌曲ID      | `"s001"`                |
| feedback  | string   | 用户反馈         | `"positive"`            |


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
    "energy": 0.3
  },
  "song_id": "s001",
  "feedback": "positive"
}
```

---

## 接口列表

---

### 1. `POST /api/analyze`

> 核心接口。接收用户语音 + 环境上下文，返回语音转写文本、情绪分析结果和推荐歌曲。

**Request Body**


| 字段      | 类型      | 必填  | 说明              |
| ------- | ------- | --- | --------------- |
| audio   | string  | ✅   | 音频文件的 Base64 编码 |
| context | Context | ✅   | 当前环境上下文         |


```json
{
  "audio": "<base64 encoded audio>",
  "context": {
    "hour": 2,
    "active_app": "VSCode",
    "kpm": 160,
    "backspace_ratio": 0.22
  }
}
```

**Response `200 OK`**


| 字段             | 类型      | 说明                 |
| -------------- | ------- | ------------------ |
| transcript     | string  | Whisper 转写的文本      |
| emotion        | Emotion | 情绪分析结果             |
| recommendation | Song    | 推荐的歌曲（含 file_path） |


```json
{
  "transcript": "今天有点烦",
  "emotion": {
    "emotion": "frustrated",
    "energy": 0.3,
    "need": "comfort"
  },
  "recommendation": {
    "id": "s001",
    "title": "Midnight Rain",
    "artist": "LoFi Dreams",
    "file_path": "/music/s001.mp3"
  }
}
```

**错误响应**


| 状态码 | 说明                    |
| --- | --------------------- |
| 400 | 缺少 audio 或 context 字段 |
| 422 | audio Base64 解码失败     |
| 500 | Whisper 或 LLM 服务异常    |


---

### 2. `POST /api/feedback`

> 记录用户对推荐歌曲的反馈，用于优化后续推荐。

**Request Body**


| 字段       | 类型     | 必填  | 说明   |
| -------- | ------ | --- | ---- |
| song_id  | string | ✅   | 歌曲ID |
| feedback | string | ✅   | 反馈类型 |


可选 feedback 值：


| 值             | 含义     |
| ------------- | ------ |
| `positive`    | 喜欢     |
| `negative`    | 不喜欢    |
| `too_quiet`   | 太安静了   |
| `too_sad`     | 太悲伤了   |
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


| 状态码 | 说明                    |
| --- | --------------------- |
| 400 | 缺少 song_id 或 feedback |
| 404 | song_id 不存在           |
| 422 | feedback 值不在允许范围内     |


---

### 3. `GET /api/context`

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


| 状态码 | 说明       |
| --- | -------- |
| 500 | 环境感知模块异常 |


---

### 4. `GET /api/memory`

> 查询历史记忆条目，支持分页。

**Query Parameters**


| 参数     | 类型      | 必填  | 默认值  | 说明   |
| ------ | ------- | --- | ---- | ---- |
| limit  | integer | ❌   | `20` | 每页条数 |
| offset | integer | ❌   | `0`  | 偏移量  |


**请求示例**

```
GET /api/memory?limit=10&offset=0
```

**Response `200 OK`**


| 字段      | 类型            | 说明     |
| ------- | ------------- | ------ |
| entries | MemoryEntry[] | 记忆条目列表 |
| total   | integer       | 总条数    |


```json
{
  "entries": [
    {
      "timestamp": "2025-01-15T02:30:00",
      "context": {
        "hour": 2,
        "active_app": "VSCode",
        "kpm": 160
      },
      "emotion": {
        "emotion": "frustrated",
        "energy": 0.3
      },
      "song_id": "s001",
      "feedback": "positive"
    }
  ],
  "total": 42
}
```

---

### 5. `GET /api/music/random`

> 从本地曲库中随机返回一首歌曲。

**Request**

无请求参数。

**Response `200 OK`**

```json
{
  "id": "s001",
  "title": "Midnight Rain",
  "artist": "LoFi Dreams",
  "file_path": "/music/s001.mp3"
}
```

**错误响应**


| 状态码 | 说明   |
| --- | ---- |
| 404 | 曲库为空 |


---

## 附录：推荐算法流程

```
1. 获取当前 context（时间、应用、键盘状态）
2. 从 memory 表检索相似场景（相近 hour + 相同 active_app）
3. 统计这些场景下 feedback = "positive" 的歌曲
4. 按 energy 匹配当前 emotion 的 energy 值
5. 返回匹配度最高的歌曲
```

---

## 变更记录


| 日期         | 版本   | 说明                    |
| ---------- | ---- | --------------------- |
| 2026-05-30 | v0.1 | 初始版本，基于技术设计文档提取 5 个接口 |


