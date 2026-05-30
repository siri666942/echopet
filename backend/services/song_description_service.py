"""把 Essentia 特征翻译成“歌曲本身”的检索描述。"""


def build_song_description(title: str, audio_features: dict) -> str:
    basic = audio_features.get("basic", {})
    semantic = audio_features.get("semantic", {})

    bpm = float(basic.get("bpm") or 0.0)
    loudness = float(basic.get("loudness") or 0.0)
    dynamic = float(basic.get("dynamic_complexity") or 0.0)
    centroid = float(basic.get("spectral_centroid") or 0.0)
    danceability = float(basic.get("danceability") or 0.0)
    key = basic.get("key") or "未知调性"
    scale = basic.get("scale") or "未知大小调"

    tempo_desc = "慢速" if bpm and bpm < 80 else "中速" if bpm < 130 else "快速"
    loudness_desc = "响度较低" if loudness < 0.2 else "响度中等" if loudness < 0.6 else "响度较高"
    brightness_desc = "频谱偏暗" if centroid < 1500 else "频谱明亮" if centroid > 3000 else "频谱均衡"
    dynamic_desc = "动态变化较小" if dynamic < 3 else "动态变化较丰富"
    dance_desc = "律动较弱" if danceability < 1 else "律动中等" if danceability < 2 else "律动明显"

    return (
        f"{title}：{tempo_desc}，{loudness_desc}，{brightness_desc}，"
        f"{dynamic_desc}，{dance_desc}，调性 {key} {scale}，"
        f"语义特征 {semantic}。"
    )
