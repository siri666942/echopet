"""语音转写服务。

这个文件负责把 Base64 音频转成文字。

正常路径：
    1. 前端录音
    2. 前端把音频文件转成 Base64
    3. POST /api/transcribe
    4. 这里解码 Base64
    5. 写成临时音频文件
    6. faster-whisper 读取临时文件并转写
    7. 删除临时文件
    8. 返回 transcript

失败路径：
    如果 faster-whisper 没装好，或者模型加载失败：
    - 不让服务崩
    - 返回 503，并带上明确原因
    - 不再用 200 + 空 transcript 伪装成功
"""

import asyncio
import base64
import binascii
import logging
import os
import tempfile
import threading

from fastapi import HTTPException

from backend.config import settings


logger = logging.getLogger(__name__)
_REQUIRED_MODEL_FILES = ("model.bin", "config.json")

# Whisper 模型对象。
# 模型比较重，所以不要每次请求都加载。
_model = None

# 记录模型是否加载失败过。
# 如果失败过，后续就不重复尝试，避免每次请求都卡很久。
_model_failed = False
_model_error_message = ""
_model_lock = threading.Lock()


async def transcribe(audio_base64: str, audio_format: str = "wav") -> dict:
    """把 Base64 音频转成文本。

    参数：
        audio_base64:
            前端传来的音频 Base64 字符串。

        audio_format:
            音频格式，比如 wav/mp3。

    返回：
        dict，字段包括 transcript/language/source。

    错误：
        - Base64 解码失败：422
        - 解码后为空：400
    """

    try:
        # validate=True 会严格检查 Base64 格式。
        audio_bytes = base64.b64decode(audio_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=422, detail="audio Base64 decode failed") from exc

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="audio is empty")

    # 模型加载和转写都比较重，放到后台线程，避免阻塞整个 uvicorn 进程。
    model = await asyncio.to_thread(_get_model)
    if model is None:
        detail = _model_error_message or _model_error or "faster-whisper unavailable"
        raise HTTPException(
            status_code=503,
            detail=f"transcribe backend unavailable: faster-whisper model unavailable: {detail}",
        )

    suffix = f".{audio_format.lstrip('.') or 'wav'}"
    temp_path = None
    try:
        # faster-whisper 更适合读文件路径，所以把 bytes 写到临时文件。
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        transcript, language = await asyncio.to_thread(_transcribe_file, model, temp_path)
        return {
            "transcript": transcript,
            "language": language,
            "source": "faster-whisper",
        }
    finally:
        # 临时文件必须删除，否则磁盘会慢慢堆垃圾。
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


def _get_model():
    """懒加载 faster-whisper 模型。

    第一次请求转写时才加载模型。

    返回：
        - WhisperModel 对象
        - 或 None，表示模型不可用
    """

    global _model, _model_failed, _model_error, _model_error_message

    if _model is not None:
        return _model

    if _model_failed:
        return None

    with _model_lock:
        if _model is not None:
            return _model

        if _model_failed:
            return None

        try:
            from faster_whisper import WhisperModel

            _model = WhisperModel(
                settings.whisper_model,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
            )
        except Exception as exc:
            _model_failed = True
            _model = None
            _model_error_message = f"faster-whisper import or model init failed: {exc}"

    return _model


def _transcribe_file(model, temp_path: str) -> tuple[str, str]:
    segments, info = model.transcribe(temp_path, language="zh", beam_size=5)

    # segments 是分段转写结果，把每一段文字拼起来。
    transcript = " ".join(segment.text for segment in segments).strip()
    if not transcript:
        raise HTTPException(status_code=422, detail="transcript is empty, no speech detected")

    return transcript, getattr(info, "language", "zh") or "zh"


def warmup_model() -> None:
    """启动后在后台预热转写模型，减少首次录音等待。"""

    _get_model()
