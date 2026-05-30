"""Essentia-only 音频特征提取服务。

这里不允许使用其他音频库兜底，也不允许返回人工默认特征。
如果 Essentia 或 TensorFlow 模型不可用，直接抛出 AudioFeatureExtractionError。
曲库入库层会捕获这个异常并记录入库失败，不创建 Song。
"""

from pathlib import Path
from typing import Any

from backend.config import settings


class AudioFeatureExtractionError(RuntimeError):
    """Essentia 分析失败。"""


def extract_audio_features(file_path: str) -> dict:
    """只使用 Essentia / Essentia TensorFlow 模型提取特征。"""

    path = Path(file_path)
    if not path.exists():
        raise AudioFeatureExtractionError(f"audio file does not exist: {file_path}")

    try:
        basic = _extract_basic_features(str(path))
        semantic = _extract_semantic_features(str(path))
    except AudioFeatureExtractionError:
        raise
    except Exception as exc:
        raise AudioFeatureExtractionError(str(exc)) from exc

    return {"basic": basic, "semantic": semantic}


def _extract_basic_features(file_path: str) -> dict:
    """Essentia Python API 基础特征。"""

    try:
        import essentia.standard as es
    except Exception as exc:
        raise AudioFeatureExtractionError("Essentia is not installed") from exc

    audio = es.MonoLoader(filename=file_path)()

    rhythm = es.RhythmExtractor2013(method="multifeature")(audio)
    bpm = float(rhythm[0])

    loudness = float(es.Loudness()(audio))
    dynamic_complexity, _ = es.DynamicComplexity()(audio)
    dynamic_complexity = float(dynamic_complexity)

    spectrum = es.Spectrum()(audio)
    spectral_centroid = float(es.Centroid()(spectrum))
    spectral_energy = float(sum(value * value for value in spectrum))

    danceability = float(es.Danceability()(audio)[0])

    key, scale, _ = es.KeyExtractor()(audio)

    duration = float(len(audio) / 44100.0)
    try:
        metadata = es.MetadataReader(filename=file_path)()
        sample_rate = float(metadata[8]) if len(metadata) > 8 and metadata[8] else 44100.0
        duration = float(len(audio) / sample_rate)
    except Exception:
        pass

    return {
        "duration": duration,
        "bpm": bpm,
        "loudness": loudness,
        "dynamic_complexity": dynamic_complexity,
        "spectral_centroid": spectral_centroid,
        "spectral_energy": spectral_energy,
        "danceability": danceability,
        "key": key,
        "scale": scale,
    }


def _extract_semantic_features(file_path: str) -> dict:
    """Essentia TensorFlow 模型语义特征。

    每个模型路径都必须配置，否则视为分析失败。
    不同 Essentia 模型输出形状可能不同，这里统一转成可 JSON 化的结构。
    """

    model_paths = {
        "genre": settings.essentia_genre_model_path,
        "mood": settings.essentia_mood_model_path,
        "danceability": settings.essentia_danceability_model_path,
        "arousal_valence": settings.essentia_arousal_valence_model_path,
        "voice_instrumental": settings.essentia_voice_instrumental_model_path,
        "acoustic_electronic": settings.essentia_acoustic_electronic_model_path,
    }
    missing = [name for name, path in model_paths.items() if not path]
    if missing:
        raise AudioFeatureExtractionError(
            "missing Essentia TensorFlow model paths: " + ", ".join(missing)
        )

    return {
        "genre": _predict_tensorflow_model(file_path, model_paths["genre"]),
        "mood": _predict_tensorflow_model(file_path, model_paths["mood"]),
        "danceability": _predict_tensorflow_model(file_path, model_paths["danceability"]),
        "arousal": _extract_named_value(
            _predict_tensorflow_model(file_path, model_paths["arousal_valence"]), 0
        ),
        "valence": _extract_named_value(
            _predict_tensorflow_model(file_path, model_paths["arousal_valence"]), 1
        ),
        "voice_instrumental": _predict_tensorflow_model(
            file_path, model_paths["voice_instrumental"]
        ),
        "acoustic_electronic": _predict_tensorflow_model(
            file_path, model_paths["acoustic_electronic"]
        ),
    }


def _predict_tensorflow_model(file_path: str, model_path: str | None) -> dict:
    try:
        import essentia.standard as es
    except Exception as exc:
        raise AudioFeatureExtractionError("Essentia TensorFlow support is not installed") from exc

    if not model_path:
        raise AudioFeatureExtractionError("model path is required")

    audio = es.MonoLoader(filename=file_path, sampleRate=16000)()

    # TensorflowPredictMusiCNN 是 Essentia 官方 TensorFlow 模型常用入口。
    # 如果某个模型需要专用前处理，部署时应换成对应 Essentia 模型类；
    # 这里仍然只调用 Essentia TensorFlow，不引入其他库或 fallback。
    try:
        prediction = es.TensorflowPredictMusiCNN(graphFilename=model_path)(audio)
    except Exception:
        prediction = es.TensorflowPredict(graphFilename=model_path)(audio)

    return {"raw": _to_jsonable(prediction)}


def _extract_named_value(prediction: dict, index: int) -> float:
    raw = prediction.get("raw", [])
    flat = _flatten(raw)
    if index >= len(flat):
        raise AudioFeatureExtractionError("arousal/valence model output is too short")
    return float(flat[index])


def _to_jsonable(value: Any):
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def _flatten(value) -> list[float]:
    if isinstance(value, list):
        result: list[float] = []
        for item in value:
            result.extend(_flatten(item))
        return result
    try:
        return [float(value)]
    except (TypeError, ValueError):
        return []
