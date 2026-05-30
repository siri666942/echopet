"""API 路由包。

`backend/api/` 下面每个文件负责一组 HTTP 接口：

- analyze.py: 文本分析和推荐
- transcribe.py: 音频转文本
- context.py: 环境上下文
- memory.py: 历史记忆
- player.py: 播放器状态和播放事件
- music.py: 曲库接口

main.py 会 import 这些模块，然后把它们的 router 挂到 FastAPI app 上。
"""
