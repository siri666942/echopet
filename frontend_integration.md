# EchoPet 前端接入指南

> 本文档面向前端开发者，说明如何与后端 API 配合完成完整交互链路。
>
> 后端地址：`http://localhost:8000`
>
> 前端基座：`DyberPet`

---

## 目录

- [一句话概括](#一句话概括)
- [完整交互流程](#完整交互流程)
- [接口速查表](#接口速查表)
- [接入步骤](#接入步骤)
  - [Step 1：录音并转文字](#step-1录音并转文字)
  - [Step 2：获取环境上下文](#step-2获取环境上下文)
  - [Step 3：发送分析请求](#step-3发送分析请求)
  - [Step 4：轮询播放状态](#step-4轮询播放状态)
  - [Step 5：用户反馈](#step-5用户反馈)
- [桌宠状态映射](#桌宠状态映射)
- [错误处理](#错误处理)
- [完整代码示例](#完整代码示例)

---

## 一句话概括

```
录音 → 转文字 → 发分析 → 拿到歌曲和桌宠状态 → 轮询播放 → 收集反馈
```

---

## 完整交互流程

```text
┌─────────┐                                    ┌─────────┐
│ DyberPet │                                    │ Backend │
└────┬────┘                                    └────┬────┘
     │                                              │
     │  ① 用户点击桌宠，开始录音                       │
     │                                              │
     │  ② 录音结束                                    │
     │  POST /api/transcribe ──────────────────────▶ │
     │  { audio: "<base64>", audio_format: "wav" }   │
     │                                              │
     │  ◀──────────────────────────────────────────  │
     │  { transcript: "今天有点烦" }                   │
     │                                              │
     │  ③ 获取环境信息                                │
     │  GET /api/context ─────────────────────────▶ │
     │                                              │
     │  ◀──────────────────────────────────────────  │
     │  { hour: 2, active_app: "VSCode", ... }      │
     │                                              │
     │  ④ 发送分析请求                                │
     │  POST /api/analyze ────────────────────────▶ │
     │  { text, input_source, context }              │
     │                                              │
     │  ◀──────────────────────────────────────────  │
     │  {                                           │
     │    emotion, current_state, bubble_text,       │
     │    assistant_reply, recommendation,           │
     │    play_action, player_status                 │
     │  }                                           │
     │                                              │
     │  ⑤ 前端更新桌宠状态 + 气泡文案                   │
     │  ⑥ 前端开始轮询播放状态                         │
     │  GET /api/player/status ────────────────────▶ │ (每2秒)
     │  ◀──────────────────────────────────────────  │
     │  { status: "playing", title: "...", ... }     │
     │                                              │
     │  ⑦ 用户点击反馈按钮                              │
     │  POST /api/feedback ───────────────────────▶ │
     │  { song_id: "s001", feedback: "positive" }    │
     │  ◀──────────────────────────────────────────  │
     │  { status: "ok" }                            │
     │                                              │
```

---

## 接口速查表

| 步骤 | 方法 | 路由 | 前端什么时候调 |
|------|------|------|--------------|
| ① 转文字 | POST | `/api/transcribe` | 录音结束后立即调用 |
| ② 上下文 | GET | `/api/context` | analyze 之前调用（可选，也可前端自己组装） |
| ③ 分析 | POST | `/api/analyze` | 拿到 transcript 后调用 |
| ④ 播放状态 | GET | `/api/player/status` | analyze 返回后开始轮询 |
| ⑤ 反馈 | POST | `/api/feedback` | 用户点击反馈按钮时 |
| 随机歌 | GET | `/api/music/random` | 桌宠空闲时随机播放（可选） |
| 记忆 | GET | `/api/memory` | 展示历史记录（可选） |

---

## 接入步骤

### Step 1：录音并转文字

前端录音后，将音频编码为 base64，发送给后端。

```javascript
// 假设你已经拿到了录音的 base64 数据
const audioBase64 = /* 录音结果 */;

const transcribeRes = await fetch("http://localhost:8000/api/transcribe", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    audio: audioBase64,
    audio_format: "wav",   // wav / mp3 / m4a
  }),
});

const { transcript, language } = await transcribeRes.json();
// transcript = "今天有点烦"
```

**请求**

```json
{
  "audio": "<base64 编码的音频>",
  "audio_format": "wav"
}
```

**响应**

```json
{
  "transcript": "我有点烦，来点适合现在的歌",
  "language": "zh",
  "source": "faster-whisper"
}
```

---

### Step 2：获取环境上下文

后端提供 `/api/context` 自动采集环境信息。前端也可以选择自己组装 context（比如从 DyberPet 获取当前应用信息）。

```javascript
const contextRes = await fetch("http://localhost:8000/api/context");
const context = await contextRes.json();
// context = { hour: 2, active_app: "VSCode", kpm: 160, backspace_ratio: 0.22 }
```

> **提示**：如果前端自己能拿到 `active_app`、`kpm` 等信息，可以直接组装 context 对象传给 analyze，不必单独调这个接口。

---

### Step 3：发送分析请求

这是核心接口，后端会一次性完成：情绪分析 → 歌曲推荐 → 控制 mpv 播放。

```javascript
const analyzeRes = await fetch("http://localhost:8000/api/analyze", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    text: transcript,                // 来自 Step 1
    input_source: "faster_whisper",  // 如果是用户直接打字输入，用 "text"
    context: context,                // 来自 Step 2
  }),
});

const result = await analyzeRes.json();
```

**请求**

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

**响应**

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

**前端拿到响应后要做的事：**

```javascript
// 1. 切换桌宠动画状态
dyberpet.setState(result.current_state);  // "frustrated"

// 2. 显示气泡文案
dyberpet.showBubble(result.bubble_text);

// 3. 显示 assistant 回复（可选，比如在对话框里）
showChatMessage(result.assistant_reply);

// 4. 开始轮询播放状态（见 Step 4）
startPollingPlayerStatus();
```

---

### Step 4：轮询播放状态

analyze 返回后，mpv 可能还在 loading。前端需要轮询 `/api/player/status` 来同步播放状态。

```javascript
let pollingTimer = null;

function startPollingPlayerStatus() {
  pollingTimer = setInterval(async () => {
    const res = await fetch("http://localhost:8000/api/player/status");
    const status = await res.json();

    // 更新 UI
    updatePlayerUI(status);

    // 如果播放结束或出错，停止轮询
    if (status.status === "idle" || status.status === "error") {
      clearInterval(pollingTimer);
    }
  }, 2000);  // 每 2 秒轮询一次
}
```

**响应**

```json
{
  "player": "mpv",
  "status": "playing",
  "track_id": "s001",
  "title": "Midnight Rain",
  "artist": "LoFi Dreams"
}
```

`status` 可选值：

| 值 | 含义 | 前端建议 |
|----|------|---------|
| `idle` | 没有播放 | 显示默认状态，停止轮询 |
| `loading` | 加载中 | 显示加载动画 |
| `playing` | 正在播放 | 显示播放中状态 |
| `paused` | 已暂停 | 显示暂停图标 |
| `error` | 播放出错 | 显示错误提示，停止轮询 |

---

### Step 5：用户反馈

用户可以对当前播放的歌曲给出反馈。反馈会写入记忆，影响后续推荐。

```javascript
async function submitFeedback(songId, feedbackType) {
  const res = await fetch("http://localhost:8000/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      song_id: songId,       // 来自 analyze 响应的 recommendation.id
      feedback: feedbackType,
    }),
  });

  const result = await res.json();
  // { status: "ok", message: "Feedback recorded" }
}
```

**feedback 可选值**

| 值 | 含义 | 前端按钮文案建议 |
|----|------|----------------|
| `positive` | 喜欢 | 👍 喜欢 |
| `negative` | 不喜欢 | 👎 不喜欢 |
| `too_quiet` | 太安静了 | 🔇 太安静了 |
| `too_sad` | 太悲伤了 | 😢 太悲伤了 |
| `more_energy` | 想要更有力量 | ⚡ 更有力量 |

---

## 桌宠状态映射

`analyze` 返回的 `current_state` 直接对应 DyberPet 的动画状态：

| current_state | 桌宠表现 | 场景 |
|--------------|---------|------|
| `idle` | 默认待机 | 没有明确情绪 |
| `focus` | 轻微呼吸动画 | 专注工作 |
| `tired` | 打哈欠 | 深夜疲劳 |
| `frustrated` | 皱眉 | Debug 红温 |
| `sad` | 缩成一团 | 情绪低落 |

---

## 错误处理

所有接口在出错时返回统一格式：

```json
{
  "detail": "错误描述"
}
```

| 状态码 | 含义 | 前端处理建议 |
|--------|------|-------------|
| 400 | 参数缺失 | 提示用户重新输入 |
| 404 | 资源不存在（如曲库为空） | 提示"暂无歌曲" |
| 422 | 参数格式错误 | 检查传参 |
| 500 | 服务端异常 | 提示"服务暂时不可用" |

建议前端统一封装请求函数：

```javascript
async function api(path, options = {}) {
  const res = await fetch(`http://localhost:8000${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "未知错误" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// 使用
const result = await api("/api/analyze", {
  method: "POST",
  body: JSON.stringify({ text, input_source, context }),
});
```

---

## 完整代码示例

把上面所有步骤串起来：

```javascript
// === 完整的一次交互 ===

async function handleVoiceInput(audioBase64) {
  try {
    // 1. 转文字
    const { transcript } = await api("/api/transcribe", {
      method: "POST",
      body: JSON.stringify({ audio: audioBase64, audio_format: "wav" }),
    });

    // 2. 获取上下文（如果前端自己有，可跳过这步）
    const context = await api("/api/context");

    // 3. 分析 + 推荐
    const result = await api("/api/analyze", {
      method: "POST",
      body: JSON.stringify({
        text: transcript,
        input_source: "faster_whisper",
        context,
      }),
    });

    // 4. 更新桌宠
    dyberpet.setState(result.current_state);
    dyberpet.showBubble(result.bubble_text);

    // 5. 轮询播放状态
    startPollingPlayerStatus();

    // 6. 保存 song_id 供反馈用
    currentSongId = result.recommendation.id;

  } catch (err) {
    dyberpet.showBubble("出了点问题，稍后再试试");
    console.error("交互失败:", err);
  }
}

// === 用户点击反馈按钮 ===
async function onFeedbackClick(type) {
  if (!currentSongId) return;
  try {
    await api("/api/feedback", {
      method: "POST",
      body: JSON.stringify({ song_id: currentSongId, feedback: type }),
    });
    dyberpet.showBubble("收到~");
  } catch (err) {
    console.error("反馈失败:", err);
  }
}

// === 用户直接打字输入（不走录音） ===
async function handleTextInput(text) {
  const context = await api("/api/context");
  const result = await api("/api/analyze", {
    method: "POST",
    body: JSON.stringify({
      text,
      input_source: "text",   // 注意这里用 "text" 不是 "faster_whisper"
      context,
    }),
  });
  // 同上，更新桌宠 + 轮询 + 保存 song_id
  dyberpet.setState(result.current_state);
  dyberpet.showBubble(result.bubble_text);
  startPollingPlayerStatus();
  currentSongId = result.recommendation.id;
}
```
