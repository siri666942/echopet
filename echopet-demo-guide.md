# EchoPet Demo 启动说明

更新时间：2026-05-30

## 1. 你现在拿到的版本能做什么

这版已经把 EchoPet 的前端适配层接进了 `DyberPet`：

- 右键桌宠菜单里新增了 `Open EchoPet Input`
- 可以打开一个最小输入面板
- 可以直接输入一句话，触发桌宠状态反馈
- 如果本地后端 `http://localhost:8000` 已启动，会优先走真实 API
- 如果后端没启动，会自动回退到本地 mock，依然可以演示
- 输入面板里还提供了 `idle / focus / tired / frustrated / sad` 的 Demo 快捷切换按钮

也就是说：

- 现在已经可以先演示前端主链路
- 后面只要把后端服务起起来，就能直接联调，不需要再重做前端结构

---

## 2. 代码改了哪些位置

### 2.1 主要新增目录

新增目录：

- `DyberPet-main/frontend/`

里面包含：

- `agent_client.py`
  - 负责调用 EchoPet 后端 API
  - 自动在 API 不可用时回退到 mock 数据
- `state_mapper.py`
  - 负责把后端返回映射成前端状态
- `input_panel.py`
  - 最小输入窗
- `player_status_poller.py`
  - 定时轮询播放器状态
- `whisper_adapter.py`
  - 负责调用后端的 `/api/transcribe`
- `audio_recorder.py`
  - 负责本地录音

### 2.2 主要改动文件

- `DyberPet-main/DyberPet/DyberPet.py`
  - 增加 EchoPet 前端适配层初始化
  - 增加输入面板打开逻辑
  - 增加提交文本逻辑
  - 增加状态映射和气泡展示
  - 增加播放器状态刷新
  - 在右键菜单里新增 EchoPet 入口

---

## 3. 当前项目结构

推荐你后面主要只看这几块：

```text
echopet/
├─ api_docs.md
├─ frontend-hackathon-flow.md
├─ dyberpet-frontend-points.md
├─ echopet-demo-guide.md
├─ product_design.md
├─ techneque_design.md
└─ DyberPet-main/
   ├─ run_DyberPet.py
   ├─ frontend/
   │  ├─ __init__.py
   │  ├─ agent_client.py
   │  ├─ input_panel.py
   │  ├─ player_status_poller.py
   │  ├─ state_mapper.py
   │  └─ whisper_adapter.py
   ├─ DyberPet/
   │  ├─ DyberPet.py
   │  └─ bubbleManager.py
   └─ res/
      └─ role/
```

---

## 4. 怎么启动 Demo

## 4.1 先准备环境

参考 `DyberPet-main/README.md`，Windows 下至少需要这些依赖：

```bash
conda create --name Dyber_pyside python=3.9.18
conda activate Dyber_pyside
conda install -c conda-forge apscheduler
conda install -c conda-forge pynput
pip install PySide6-Fluent-Widgets==1.5.4 -i https://pypi.org/simple/
pip install pyside6==6.5.2
pip install tendo
```

如果你已经能正常跑原版 `DyberPet`，一般说明环境已经差不多齐了。

## 4.2 启动桌宠前端

进入目录：

```bash
cd c:\Users\thyss\Documents\GitHub\echopet\DyberPet-main
py -3.9 run_DyberPet.py
```

启动后：

1. 桌面上会出现桌宠
2. 右键桌宠
3. 点击 `Open EchoPet Input`
4. 输入一句话或直接点面板里的状态按钮

## 4.3 录音与转写链路

现在已经按最新接入文档对齐：

- 录音结束后，前端会调用 `http://localhost:8000/api/transcribe`
- 后端负责把音频转成文本
- 前端拿到 transcript 后只回填输入框
- 用户点击 `提交` 后，前端再把最终文本发给 `/api/analyze`

也就是说：

- 不再需要单独启动 `FastWhisperAPI`
- 只需要把你们自己的主后端起在 `8000`

---

## 5. 怎么演示

## 5.1 不起后端时

这是当前最稳的展示方式。

操作：

1. 启动 `DyberPet`
2. 右键打开 `Open EchoPet Input`
3. 直接输入：
   - `我有点烦，来点适合现在的歌`
   - `我想专注一下`
   - `今天有点累`
4. 或直接点击：
   - `专注`
   - `疲惫`
   - `烦躁`
   - `低落`
5. 也可以点击 `开始录音`
6. 再点一次 `停止录音`

效果：

- 前端会自动生成 mock 分析结果
- 桌宠会弹出气泡
- 面板会更新状态、回复和推荐歌曲
- 如果主后端已启动并实现 `/api/transcribe`，录音会自动回填到文本框

## 5.2 起后端时

如果你的后端服务已经在：

- `http://localhost:8000`

那么前端会自动优先调用：

- `GET /api/context`
- `POST /api/analyze`
- `GET /api/player/status`
- `POST /api/feedback`

也就是说，不需要改前端配置，后端起好后直接联调即可。

---

## 6. 当前版本的边界

这版已经能支撑第一轮 Demo，但仍然属于“前端骨架版”：

- 已完成：
  - 输入面板
  - mock/API 双模式
  - 状态映射
  - 菜单入口
  - 播放状态轮询
  - 反馈按钮基础接线
  - 录音后调用 `/api/transcribe` 并回填文本框

- 还没完成：
  - 角色资源状态图替换
  - 推荐卡片更完整的视觉样式
  - 更细的播放器反馈 UI

---

## 7. 下一步最建议继续改什么

如果你接下来继续推进，我建议按这个顺序往下做：

1. 给你们自己的角色补 5 个状态素材
2. 把 `focus/tired/frustrated/sad` 映射到真实动作资源
3. 给录音链路加更稳定的权限/设备提示
4. 把推荐结果做成更明显的展示卡片
5. 接好 `POST /api/feedback` 的完整交互提示
6. 继续优化角色资源和状态动作

---

## 8. 最关键的文件位置

你后面最常改的文件大概率就是这些：

- `c:/Users/thyss/Documents/GitHub/echopet/DyberPet-main/run_DyberPet.py`
- `c:/Users/thyss/Documents/GitHub/echopet/DyberPet-main/DyberPet/DyberPet.py`
- `c:/Users/thyss/Documents/GitHub/echopet/DyberPet-main/DyberPet/bubbleManager.py`
- `c:/Users/thyss/Documents/GitHub/echopet/DyberPet-main/frontend/agent_client.py`
- `c:/Users/thyss/Documents/GitHub/echopet/DyberPet-main/frontend/input_panel.py`
- `c:/Users/thyss/Documents/GitHub/echopet/DyberPet-main/frontend/audio_recorder.py`
- `c:/Users/thyss/Documents/GitHub/echopet/DyberPet-main/frontend/state_mapper.py`
- `c:/Users/thyss/Documents/GitHub/echopet/DyberPet-main/frontend/player_status_poller.py`
- `c:/Users/thyss/Documents/GitHub/echopet/DyberPet-main/frontend/whisper_adapter.py`

---

## 9. 一句话总结

现在这版已经把 EchoPet 从“纯方案”推进到了“可启动、可演示、可继续联调”的前端骨架状态。
