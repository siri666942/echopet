# EchoPet

更新时间：2026-05-30

## 项目简介

EchoPet 是一个桌面情绪音乐 Agent Demo。

目标是实现这样一条主链路：

```text
用户说一句话 / 输入一句话
→ 桌宠理解当前状态
→ 结合环境与记忆
→ 自动推荐并播放更适合当下的音乐
```

当前前端基座使用 `DyberPet`，并在其上增加 EchoPet 的前端适配层。

---

## 当前技术路线

- 前端基座：`DyberPet`
- 环境感知：`ActivityWatch`
- 语音转写：后端 `POST /api/transcribe`
- 分析编排：后端 `POST /api/analyze`
- 播放执行：后端控制 `mpv`
- 前端职责：输入、状态展示、推荐展示、播放状态展示、反馈

---

## 当前进展

当前已经完成一版可演示的前端骨架：

- 已接入 EchoPet 输入面板
- 已支持文本输入
- 已支持本地录音并调用 `/api/transcribe`
- 已支持调用 `/api/analyze`
- 已支持桌宠状态映射和气泡反馈
- 已支持推荐歌曲信息展示
- 已支持轮询 `/api/player/status`
- 已支持调用 `/api/feedback`
- 后端不可用时可回退到本地 mock 演示

---

## 快速启动

### 1. 安装依赖

建议使用 Python 3.9：

```bash
conda create --name Dyber_pyside python=3.9.18
conda activate Dyber_pyside
conda install -c conda-forge apscheduler
conda install -c conda-forge pynput
pip install PySide6-Fluent-Widgets==1.5.4 -i https://pypi.org/simple/
pip install pyside6==6.5.2
pip install tendo
```

### 2. 启动桌宠前端

```bash
cd c:\Users\thyss\Documents\GitHub\echopet\DyberPet-main
py -3.9 run_DyberPet.py
```

启动后：

1. 右键桌宠
2. 点击 `Open EchoPet Input`
3. 输入一句话，或者使用录音按钮

### 3. 启动后端

后端默认地址：

- `http://localhost:8000`

前端会按以下接口联调：

- `POST /api/transcribe`
- `GET /api/context`
- `POST /api/analyze`
- `GET /api/player/status`
- `POST /api/feedback`

---

## 关键文档

- [产品方案](file:///c:/Users/thyss/Documents/GitHub/echopet/product_design.md)
- [接口文档](file:///c:/Users/thyss/Documents/GitHub/echopet/api_docs.md)
- [前端接入指南](file:///c:/Users/thyss/Documents/GitHub/echopet/frontend_integration.md)
- [Demo 启动说明](file:///c:/Users/thyss/Documents/GitHub/echopet/echopet-demo-guide.md)
- [前端开发进度](file:///c:/Users/thyss/Documents/GitHub/echopet/frontend-development-progress.md)
- [前端开发流程](file:///c:/Users/thyss/Documents/GitHub/echopet/frontend-hackathon-flow.md)

---

## 项目结构

```text
echopet/
├─ README.md
├─ api_docs.md
├─ frontend_integration.md
├─ product_design.md
├─ echopet-demo-guide.md
├─ frontend-development-progress.md
├─ frontend-hackathon-flow.md
└─ DyberPet-main/
   ├─ run_DyberPet.py
   ├─ frontend/
   ├─ DyberPet/
   ├─ res/
   └─ docs/
```

---

## 说明

- `DyberPet-main` 目录保留的是运行桌宠前端所需的代码和资源
- 其原始上游框架是 `DyberPet`，但当前仓库已经按 EchoPet Demo 的需要进行了前端适配
- `mpv` 的播放控制不在前端实现，由后端负责
