# DyberPet 前端改造点位说明

更新时间：2026-05-30

## 文档目的

这份文档用于回答两个问题：

1. `DyberPet` 在这个黑客松项目里到底该改哪里
2. 前端如何和当前 API 文档 `[api_docs.md](file:///c:/Users/thyss/Desktop/14/api_docs.md)` 对齐

这份说明默认已经和下面两份文档保持一致：

- [frontend-hackathon-flow.md](file:///c:/Users/thyss/Desktop/14/frontend-hackathon-flow.md)
- [api_docs.md](file:///c:/Users/thyss/Desktop/14/api_docs.md)

---

## 先给结论

`DyberPet` 在你们项目里应该扮演：

- 桌宠前端基座
- 状态展示层
- 输入入口层
- 推荐反馈展示层

它**不应该**扮演：

- LLM 编排层
- 记忆系统主逻辑层
- 环境感知计算层
- `mpv` 控制核心层

一句话：

**`DyberPet` 做“身体和脸”，后端 Agent 做“大脑”。**

---

## 现在选定的主链路

当前已经确定的链路是：

```text
用户文本输入 / 录音
    ↓
faster-whisper
    ↓
text
    ↓
GET /api/context
    ↓
POST /api/analyze
    ↓
DyberPet 切状态 + 展示气泡 + 展示推荐
    ↓
后端控制 mpv
    ↓
GET /api/player/status
    ↓
前端展示播放状态
```

所以前端要做的不是“直接理解用户”，而是：

- 把输入整理成统一文本
- 调后端接口
- 把后端结果映射成桌宠表现

---

## 现有代码里的核心改造点

你真正最应该看的地方，主要就 3 个：

### 1. 应用装配入口

- [run_DyberPet.py](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/run_DyberPet.py)

这里适合挂：

- 你们新增的前端适配层对象
- 定时轮询播放器状态
- 前端面板和主桌宠之间的信号连接

当前可以重点关注的装配位置：

- [DyberPetApp.__connectSignalToSlot](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/run_DyberPet.py#L84-L119)

这是最适合接入你们自定义模块的地方。

### 2. 桌宠主逻辑

- [DyberPet.py](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/DyberPet.py)

这里适合挂：

- 输入入口打开逻辑
- 状态映射逻辑
- 推荐反馈展示
- 新增菜单动作
- 新增前端方法，例如 `apply_agent_result()`

当前优先关注的点：

- [PetWidget](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/DyberPet.py#L351-L388)
- [_set_menu](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/DyberPet.py#L790-L812)
- [_set_Statusmenu](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/DyberPet.py#L882-L1026)
- [_show_Staus_menu](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/DyberPet.py#L1034-L1040)
- [register_bubbleText](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/DyberPet.py#L1380-L1381)
- [_change_status](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/DyberPet.py#L1390-L1427)

### 3. 气泡系统

- [bubbleManager.py](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/bubbleManager.py)

这里适合挂：

- 新业务气泡类型
- 气泡文案模板
- 用户昵称替换

当前优先关注的点：

- [load_bubble_config](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/bubbleManager.py#L70-L88)
- [trigger_bubble](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/bubbleManager.py#L97-L120)

---

## 我建议新增的前端模块

不要把所有代码继续堆在 `DyberPet.py` 里。

建议在项目里新增一个轻量目录，例如：

```text
DyberPet-main/DyberPet-main/frontend/
  agent_client.py
  state_mapper.py
  input_panel.py
  whisper_adapter.py
  player_status_poller.py
```

每个文件负责的事情如下。

### `agent_client.py`

负责：

- 请求 `GET /api/context`
- 请求 `POST /api/analyze`
- 请求 `POST /api/feedback`
- 请求 `GET /api/player/status`

不负责：

- UI
- 状态动画
- 音频录制

### `state_mapper.py`

负责把后端结果映射成前端可用结构，例如：

```python
{
    "pet_state": "frustrated",
    "bubble_text": "你现在有点紧绷，我先放一点柔和的。",
    "ui_tag": "comfort",
    "playback_hint": "loading"
}
```

它的作用是隔离后端字段和前端动作名，避免以后接口改一点，`DyberPet.py` 到处都要改。

### `input_panel.py`

负责：

- 小悬浮输入窗
- 文本输入框
- 录音按钮
- “识别中”提示
- 识别结果预览
- 提交按钮

这是你前端最关键的新 UI。

### `whisper_adapter.py`

负责：

- 录音文件准备
- 调 `POST /api/transcribe`
- 返回 transcript

注意：

- 这一层只做“音频 -> 文本”
- 不做情绪分析
- 不做推荐

### `player_status_poller.py`

负责：

- 定时轮询 `GET /api/player/status`
- 把 `mpv` 当前状态回传给桌宠 UI

这样你就不需要让桌宠自己控制 `mpv`。

---

## 建议新增的前端方法

以下方法不一定都要今天写完，但建议按这个方向组织。

### 在 `PetWidget` 里新增

#### `open_input_panel()`

负责：

- 打开悬浮输入窗
- 定位在桌宠附近

建议挂载位置：

- 通过右键菜单新增一个入口
- 或后续再加双击桌宠打开

#### `submit_user_text(text, input_source)`

负责：

- 调 `agent_client`
- 请求上下文
- 请求 analyze
- 等待结果返回

#### `apply_agent_result(result)`

负责：

- 切换桌宠状态
- 显示气泡
- 刷新推荐卡
- 刷新播放提示

这是整个前端链路最关键的方法。

#### `update_player_status(status_payload)`

负责：

- 接收播放器状态
- 更新“正在播放 / 已暂停 / 播放失败”的显示

#### `send_feedback(song_id, feedback)`

负责：

- 触发 `POST /api/feedback`
- 根据结果显示轻提示

---

## 现有代码各点位怎么用

下面这部分是最重要的实操说明。

## 点位 1：在菜单里挂输入入口

推荐修改位置：

- [_set_Statusmenu](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/DyberPet.py#L1002-L1026)

原因：

- 这里已经是主交互入口
- 已经有 `Dashboard` 和 `System` 菜单项
- 最容易新增一个“和 EchoPet 说句话”或“打开输入框”

推荐新增：

- `打开输入框`
- `查看当前推荐`
- `刷新播放器状态`

不建议一开始放太多入口。

## 点位 2：在主窗体里保存前端适配对象

推荐修改位置：

- [PetWidget.__init__](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/DyberPet.py#L388-L448)

这里适合增加：

- `self.agent_client`
- `self.input_panel`
- `self.whisper_adapter`
- `self.player_status_poller`
- `self.current_track`
- `self.current_agent_state`

这样桌宠主对象就能统一拿到这些能力，但仍然不把业务实现写死在这里。

## 点位 3：沿用现有气泡能力，不重做

推荐修改位置：

- [register_bubbleText](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/DyberPet.py#L1380-L1381)
- [trigger_bubble](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/bubbleManager.py#L97-L120)

建议做法：

- 先保留系统气泡逻辑
- 业务气泡优先用 `bubble_text` 直接显示
- 需要角色化再在 `bubble_conf.json` 中补模板

换句话说：

- 先能显示
- 再做美化

## 点位 4：不要复用 `_change_status()` 做 Agent 主状态

推荐关注位置：

- [_change_status](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/DyberPet.py#L1390-L1427)

注意：

- 这个方法当前是给饱食度和好感度系统用的
- 它不是你们这次 `focus/tired/frustrated/sad` 业务状态的理想入口

建议：

- 新增一套独立方法，例如 `apply_pet_state(state_name)`
- 不要把 Agent 状态强塞进 HP/FV 逻辑

## 点位 5：应用装配时接轮询器

推荐修改位置：

- [DyberPetApp.__connectSignalToSlot](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/run_DyberPet.py#L84-L119)

这里适合做：

- 把输入窗信号接到 `PetWidget.submit_user_text`
- 把播放器状态轮询结果接到 `PetWidget.update_player_status`
- 把推荐卡片或提示信号接回桌宠 UI

这是前端层最适合做“总装配”的地方。

---

## API 对齐说明

当前这份点位说明，已经按 [api_docs.md](file:///c:/Users/thyss/Desktop/14/api_docs.md) 新版本对齐。

### 前端最相关的接口只有 5 个

1. `POST /api/transcribe`
2. `POST /api/analyze`
3. `POST /api/feedback`
4. `GET /api/context`
5. `GET /api/player/status`

### 前端应该怎么调用

#### 情况 A：用户直接输入文本

```text
input_panel
  -> GET /api/context
  -> POST /api/analyze
  -> apply_agent_result
```

#### 情况 B：用户点击录音

```text
input_panel
  -> POST /api/transcribe
  -> transcript 回填输入框
  -> GET /api/context
  -> POST /api/analyze
  -> apply_agent_result
```

#### 情况 C：播放器状态刷新

```text
player_status_poller
  -> GET /api/player/status
  -> update_player_status
```

### 前端应该依赖哪些返回字段

来自 `POST /api/analyze`：

- `transcript`
- `current_state`
- `bubble_text`
- `assistant_reply`
- `recommendation`
- `play_action`
- `player_status`

来自 `GET /api/player/status`：

- `status`
- `track_id`
- `title`
- `artist`

---

## 前端状态映射建议

建议你在 `state_mapper.py` 里收敛成前端自己的状态，不要直接把后端的所有情绪值原样用掉。

### 推荐映射

| 后端 emotion | 前端 pet_state |
|---|---|
| `focused` | `focus` |
| `tired` | `tired` |
| `frustrated` | `frustrated` |
| `sad` | `sad` |
| `calm` / `happy` / 其他 | `idle` |

这样前端资源和动作管理会简单很多。

---

## 具体开发顺序

## 第一步：只做 UI 壳子

目标：

- 输入窗能打开
- 能输入文本
- 能显示一条假气泡

这一步不要接任何真实 API。

## 第二步：接假结果

目标：

- 提交一句话后，返回一份本地 mock 结果
- 能驱动 `apply_agent_result`

这一步先把状态切换和推荐卡跑通。

## 第三步：接 `POST /api/transcribe`

目标：

- 录音结束后能看到识别文本
- 文本能回填到输入框

这一步只打通“音频 -> 文本”。

## 第四步：接 `GET /api/context` + `POST /api/analyze`

目标：

- 用户提交文本后
- 能拿到推荐结果
- 能触发桌宠反馈

## 第五步：接 `GET /api/player/status`

目标：

- 播放器状态能轮询显示
- 前端能明确告诉用户“已经播了”

## 第六步：接 `POST /api/feedback`

目标：

- 喜欢 / 不喜欢 / 换一首按钮可用

---

## 最小可改文件清单

如果你想尽量少动，优先只改这些：

- [run_DyberPet.py](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/run_DyberPet.py)
- [DyberPet.py](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/DyberPet.py)
- [bubbleManager.py](file:///c:/Users/thyss/Desktop/14/DyberPet-main/DyberPet-main/DyberPet/bubbleManager.py)
- `frontend/agent_client.py`
- `frontend/input_panel.py`
- `frontend/whisper_adapter.py`
- `frontend/state_mapper.py`
- `frontend/player_status_poller.py`

---

## 你前端现在最值得立刻做的事

按优先级，我建议你马上推进这 5 项：

1. 在菜单里加“打开输入框”
2. 做一个最小 `input_panel`
3. 做一个 `apply_agent_result()` 的假数据版本
4. 做 `state_mapper.py`
5. 再去接 `api_docs.md` 里这 5 个核心接口

这样推进是最稳的。

---

## 我对你这部分的最终判断

如果你是前端负责人，这份文档应该能帮你把任务拆成一句话：

**你不是在重写桌宠，而是在 `DyberPet` 上加一层“输入、状态映射、结果展示”的前端适配层。**

只要守住这个边界，项目就不容易做乱。
