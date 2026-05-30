# EchoPet 技术设计文档

---

# 技术架构

                ┌────────────┐
                │   Frontend │
                │  Desktop   │
                │    Pet     │
                └─────┬──────┘
                      │
                 HTTP API
                      │
                ┌─────▼──────┐
                │  Backend   │
                │   Agent    │
                └─────┬──────┘
                      │
     ┌────────────────┼───────────────┐
     │                │               │
     ▼                ▼               ▼

 Environment      Memory         Music Library

---

# 技术栈

## Frontend

推荐：

- Electron
- React
- TypeScript

或：

- Tauri
- React

---

## Backend

推荐：

- Python
- FastAPI

---

## Database

- SQLite

---

## AI能力

- Whisper（语音转文字）
- GPT / Claude（情绪分析）

---

# 模块划分

## Frontend

负责：

- 桌宠UI
- 录音
- 状态展示
- 音乐播放
- 用户反馈

不负责：

- Memory
- 推荐算法
- 环境感知

---

## Backend

负责：

- Whisper调用
- LLM调用
- 环境感知
- Memory
- 推荐器
- 曲库管理

---

# 数据流

用户语音

↓

Whisper

↓

文本

↓

环境感知

↓

Memory检索

↓

LLM分析

↓

推荐器

↓

返回歌曲

↓

用户反馈

↓

Memory更新

---

# 数据模型

## Context

```json
{
  "hour": 2,
  "active_app": "VSCode",
  "kpm": 160,
  "backspace_ratio": 0.22
}