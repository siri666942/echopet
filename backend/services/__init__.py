"""业务服务包。

API 层只负责接 HTTP 请求，不直接写复杂业务。

真正的业务逻辑放在 services 里：

- emotion_service: 情绪分析
- recommender: 歌曲推荐
- memory_service: 记忆读写
- music_service: 曲库管理
- player_service: mpv 播放控制
- whisper_service: 语音转写
- context_service: 环境感知
"""
