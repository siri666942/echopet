"""测试 Essentia-only 音频特征服务的失败行为。"""

import pytest

from backend.services.audio_feature_service import (
    AudioFeatureExtractionError,
    extract_audio_features,
)


def test_extract_audio_features_rejects_missing_file():
    with pytest.raises(AudioFeatureExtractionError):
        extract_audio_features("C:/definitely/missing/audio.mp3")
