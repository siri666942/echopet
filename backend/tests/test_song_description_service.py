"""测试歌曲描述生成。"""

from backend.services.song_description_service import build_song_description


def test_build_song_description_uses_essentia_features():
    description = build_song_description(
        "Track",
        {
            "basic": {
                "bpm": 95,
                "loudness": 0.4,
                "dynamic_complexity": 2.0,
                "spectral_centroid": 3200,
                "danceability": 1.5,
                "key": "C",
                "scale": "major",
            },
            "semantic": {
                "genre": {"raw": {"ambient": 0.8}},
                "mood": {"raw": {"calm": 0.7}},
                "arousal": 0.3,
                "valence": 0.6,
                "voice_instrumental": {"raw": {"instrumental": 0.9}},
            },
        },
    )

    assert "中速" in description
    assert "响度中等" in description
    assert "频谱明亮" in description
    assert "语义特征" in description
    assert "适合" not in description
