"""Simple Qt audio recorder that captures PCM and emits wav bytes."""

from __future__ import annotations

import io
import wave

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QObject, Signal
from PySide6.QtMultimedia import QAudioFormat, QAudioSource, QMediaDevices


class AudioRecorder(QObject):
    recording_started = Signal()
    recording_finished = Signal(bytes, str)
    recording_failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_device = None
        self.audio_format = None
        self.audio_source = None
        self.audio_buffer = None
        self.audio_bytes = QByteArray()
        self.is_recording = False
        self._build_session()

    def _build_session(self) -> None:
        try:
            device = QMediaDevices.defaultAudioInput()
            if getattr(device, "isNull", lambda: False)():
                raise RuntimeError("未检测到可用麦克风")

            audio_format = QAudioFormat()
            audio_format.setSampleRate(16000)
            audio_format.setChannelCount(1)
            audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

            if not device.isFormatSupported(audio_format):
                preferred = device.preferredFormat()
                if preferred.sampleFormat() == QAudioFormat.SampleFormat.Float:
                    raise RuntimeError("当前麦克风默认格式不支持 Int16 PCM 录音")
                audio_format = preferred

            self.audio_device = device
            self.audio_format = audio_format
            self.audio_source = QAudioSource(device, audio_format, self)
        except Exception as exc:  # pragma: no cover - runtime hardware guard
            self.recording_failed.emit(f"录音初始化失败: {exc}")

    def toggle(self) -> None:
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self) -> None:
        if self.is_recording:
            return
        if self.audio_source is None or self.audio_format is None:
            self.recording_failed.emit("录音器不可用")
            return

        self.is_recording = True
        self.audio_bytes = QByteArray()
        self.audio_buffer = QBuffer(self.audio_bytes, self)
        self.audio_buffer.open(QIODevice.WriteOnly)

        try:
            self.audio_source.start(self.audio_buffer)
            self.recording_started.emit()
        except Exception as exc:  # pragma: no cover - runtime hardware guard
            self.is_recording = False
            if self.audio_buffer is not None:
                self.audio_buffer.close()
            self.recording_failed.emit(f"开始录音失败: {exc}")

    def stop_recording(self) -> None:
        if not self.is_recording:
            return
        self.is_recording = False
        try:
            self.audio_source.stop()
            if self.audio_buffer is not None:
                self.audio_buffer.close()
        except Exception as exc:  # pragma: no cover - runtime hardware guard
            self.recording_failed.emit(f"停止录音失败: {exc}")
            return
        self._flush_recording()

    def _flush_recording(self) -> None:
        pcm_bytes = bytes(self.audio_bytes.data())
        if not pcm_bytes:
            self.recording_failed.emit("录音为空，通常是 Qt 录音流没有拿到麦克风数据")
            return
        try:
            wav_bytes = self._build_wav_bytes(pcm_bytes)
            self.recording_finished.emit(wav_bytes, "wav")
        except Exception as exc:  # pragma: no cover - runtime hardware guard
            self.recording_failed.emit(f"读取录音失败: {exc}")
        finally:
            self.audio_buffer = None
            self.audio_bytes = QByteArray()

    def _build_wav_bytes(self, pcm_bytes: bytes) -> bytes:
        if self.audio_format is None:
            raise RuntimeError("音频格式未初始化")

        sample_format = self.audio_format.sampleFormat()
        sample_width_map = {
            QAudioFormat.SampleFormat.UInt8: 1,
            QAudioFormat.SampleFormat.Int16: 2,
            QAudioFormat.SampleFormat.Int32: 4,
        }
        if sample_format not in sample_width_map:
            raise RuntimeError("当前录音格式暂不支持导出 wav")

        with io.BytesIO() as buffer:
            with wave.open(buffer, "wb") as wav_file:
                wav_file.setnchannels(self.audio_format.channelCount())
                wav_file.setsampwidth(sample_width_map[sample_format])
                wav_file.setframerate(self.audio_format.sampleRate())
                wav_file.writeframes(pcm_bytes)
            return buffer.getvalue()
