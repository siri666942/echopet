"""业务服务包。

API 层只负责接 HTTP 请求，不直接写复杂业务。

真正的业务逻辑放在 services 里：

- intent_service: 把用户上下文翻译成音乐检索语言
- embedding_service: 调用真实 embedding API，并提供 cosine similarity
- audio_feature_service: 提取真实音频特征
- song_description_service: 把音频特征转成歌曲描述
- recommender: embedding 召回和重排
- playlist_service: 当前播放队列
- profile_service: 长期用户画像
- play_session_service: 播放会话和隐式反馈
- memory_service: 记忆读写
- music_service: 曲库管理
- player_service: mpv 播放控制
- whisper_service: 语音转写
- context_service: 环境感知
- emotion_service: 兼容保留，不再作为推荐主链路
"""
