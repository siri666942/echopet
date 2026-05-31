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
    """Essentia TensorFlow 语义特征。

    Essentia 的很多分类模型不是"直接吃 mp3"的模型，而是两段式：

    1. 先用官方 embedding 模型把音频变成一串向量。
       - MSD MusicNN embedding 用于情绪、舞曲性、人声/器乐、唤醒度/愉悦度。
       - Discogs Effnet embedding 用于 Discogs 400 风格分类和 acoustic/electronic。

    2. 再把 embedding 喂给对应 classification head。

    这里仍然只使用 Essentia / Essentia TensorFlow。
    如果任何模型文件缺失或推理失败，直接抛错，歌曲入库失败。
    """

    required_paths = {
        "msd_embedding": settings.essentia_msd_embedding_model_path,
        "discogs_embedding": settings.essentia_discogs_embedding_model_path,
        "genre": settings.essentia_genre_model_path,
        "mood": settings.essentia_mood_model_path,
        "danceability": settings.essentia_danceability_model_path,
        "arousal_valence": settings.essentia_arousal_valence_model_path,
        "voice_instrumental": settings.essentia_voice_instrumental_model_path,
        "acoustic_electronic": settings.essentia_acoustic_electronic_model_path,
    }
    missing = [name for name, path in required_paths.items() if not path or not Path(path).exists()]
    if missing:
        raise AudioFeatureExtractionError(
            "missing Essentia TensorFlow model files: " + ", ".join(missing)
        )

    msd_embedding = _extract_msd_musicnn_embedding(
        file_path, settings.essentia_msd_embedding_model_path
    )
    discogs_embedding = _extract_discogs_effnet_embedding(
        file_path, settings.essentia_discogs_embedding_model_path
    )

    mood_scores = _scores_from_vector(
        _predict_2d_head(msd_embedding, settings.essentia_mood_model_path),
        ["happy", "sad", "aggressive", "relaxed", "party"],
    )
    genre_scores = _top_index_scores(
        _predict_2d_head(discogs_embedding, settings.essentia_genre_model_path),
        prefix="discogs_genre",
        limit=8,
    )
    danceability_scores = _scores_from_vector(
        _predict_2d_head(msd_embedding, settings.essentia_danceability_model_path),
        ["not_danceable", "danceable"],
    )
    arousal_valence = _average_prediction(
        _predict_2d_head(msd_embedding, settings.essentia_arousal_valence_model_path)
    )
    voice_scores = _scores_from_vector(
        _predict_2d_head(msd_embedding, settings.essentia_voice_instrumental_model_path),
        ["instrumental", "voice"],
    )
    acoustic_electronic_scores = _scores_from_vector(
        _predict_2d_head(
            discogs_embedding,
            settings.essentia_acoustic_electronic_model_path,
        ),
        ["acoustic", "electronic"],
    )

    return {
        "genre": genre_scores,
        "mood": mood_scores,
        "danceability": danceability_scores,
        "arousal": _bounded_value(arousal_valence, 0),
        "valence": _bounded_value(arousal_valence, 1),
        "voice_instrumental": voice_scores,
        "acoustic_electronic": acoustic_electronic_scores,
    }


def _extract_msd_musicnn_embedding(file_path: str, model_path: str) -> Any:
    try:
        import essentia.standard as es
    except Exception as exc:
        raise AudioFeatureExtractionError("Essentia TensorFlow support is not installed") from exc

    audio = es.MonoLoader(filename=file_path, sampleRate=16000)()
    return es.TensorflowPredictMusiCNN(graphFilename=model_path, output="model/dense/BiasAdd")(audio)


def _extract_discogs_effnet_embedding(file_path: str, model_path: str) -> Any:
    try:
        import essentia.standard as es
    except Exception as exc:
        raise AudioFeatureExtractionError("Essentia TensorFlow support is not installed") from exc

    audio = es.MonoLoader(filename=file_path, sampleRate=16000)()
    return es.TensorflowPredictEffnetDiscogs(
        graphFilename=model_path,
        output="PartitionedCall:1",
    )(audio)


def _predict_2d_head(embedding: Any, model_path: str) -> Any:
    try:
        import essentia.standard as es
    except Exception as exc:
        raise AudioFeatureExtractionError("Essentia TensorFlow support is not installed") from exc

    inputs = ["serving_default_model_Placeholder", "model/Placeholder"]
    outputs = [
        "PartitionedCall",
        "StatefulPartitionedCall",
        "model/Softmax",
        "model/Sigmoid",
        "model/Identity",
        "Identity",
    ]
    last_error: Exception | None = None
    for input_name in inputs:
        for output in outputs:
            try:
                return es.TensorflowPredict2D(
                    graphFilename=model_path,
                    input=input_name,
                    output=output,
                )(embedding)
            except Exception as exc:
                last_error = exc
    raise AudioFeatureExtractionError(
        f"Essentia TensorFlow classifier failed for {model_path}: {last_error}"
    )


def _scores_from_vector(value: Any, labels: list[str]) -> dict[str, float]:
    flat = _average_prediction(value)
    if not flat:
        raise AudioFeatureExtractionError("classifier output is empty")
    scores = {}
    for index, label in enumerate(labels):
        if index < len(flat):
            scores[label] = float(flat[index])
    return scores


def _top_index_scores(value: Any, prefix: str, limit: int) -> dict[str, float]:
    flat = _average_prediction(value)
    if not flat:
        raise AudioFeatureExtractionError("classifier output is empty")
    indexed = sorted(enumerate(flat), key=lambda item: item[1], reverse=True)[:limit]
    return {f"{prefix}_{index}": float(score) for index, score in indexed}


def _bounded_value(values: list[float], index: int) -> float:
    if index >= len(values):
        raise AudioFeatureExtractionError("arousal/valence model output is too short")
    return float(values[index])


def _average_prediction(value: Any) -> list[float]:
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, list) and value and isinstance(value[0], list):
        width = len(value[0])
        if width == 0:
            return []
        return [
            float(sum(float(row[index]) for row in value if len(row) > index) / len(value))
            for index in range(width)
        ]
    return _flatten(value)


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
    if hasattr(value, "tolist"):
        return _flatten(value.tolist())
    if isinstance(value, list):
        result: list[float] = []
        for item in value:
            result.extend(_flatten(item))
        return result
    try:
        return [float(value)]
    except (TypeError, ValueError):
        return []
