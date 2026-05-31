
# EchoPet Demo 展示流程说明

## 目标

这个 Demo 用来展示：EchoPet 如何从“用户当前状态”出发，理解场景、检索音乐、播放推荐，并不断积累记忆。

---

## Demo 主线

用户深夜写代码，状态有点紧绷。

EchoPet 通过语音、键盘行为、上下文和历史偏好理解用户，并自动推荐合适音乐。

---

## 环节 1：场景引入

画面内容：

- 时间：凌晨 2 点
- 用户正在 VSCode 写代码
- 桌面旁边有 EchoPet
- 用户说：“今天 debug 一天了，有点烦”

要表达：

传统音乐软件需要用户自己找歌；EchoPet 会主动理解此刻状态。

---

## 环节 2：Observe 观察

EchoPet 收集这些信息：

```text
语音输入：今天 debug 一天了，有点烦
当前应用：VSCode
当前时间：02:00
键盘状态：高频输入、退格较多、节奏不稳定
历史偏好：喜欢 LoFi / 民谣 / 钢琴，不喜欢重金属 / 激进摇滚
输出用户当前状态：

{
  "focus": 0.72,
  "stress": 0.61,
  "fatigue": 0.35,
  "typing_state": "high_activity_unstable"
}
环节 3：Think 思考
系统把用户状态转成音乐检索意图：

中等偏低能量、节奏稳定、有支撑感、不吵、不太悲伤的器乐音乐
然后进入推荐流程：

retrieval_query
→ Embedding 召回 Top20
→ 规则重排 Top5
→ AI 最终排序
→ 生成播放队列
环节 4：Music Understanding 音乐理解
系统不是手写标签，而是分析本地音乐文件。

每首歌会生成：

{
  "bpm": 85.2,
  "loudness": -12.4,
  "arousal": 0.35,
  "valence": 0.25,
  "genre": "lofi",
  "instrumental": 0.8
}
并生成歌曲描述和 embedding，用于匹配用户需求。

环节 5：Act 执行
EchoPet 推荐并播放一首歌：

Midnight Rain
推荐理由：

节奏稳定，中低能量，有支撑感，不会打断专注。
桌宠气泡展示：

你现在有点紧，我先放点稳一点的。
环节 6：Memory 更新
播放结束后，系统记录：

{
  "time": "02:00",
  "app": "VSCode",
  "keyboard_state": "high_activity_unstable",
  "song_id": "s001",
  "completion_rate": 0.85
}
之后更新用户画像：

用户在深夜写代码、高压力状态下，更容易听完稳定节奏、LoFi、钢琴类音乐。
Demo 结尾
核心表达：

EchoPet 不只是播放器。
它通过 Observe → Think → Act，成为一个懂你当下状态的音乐 Agent。
