"""Download and validate the configured faster-whisper model."""

from __future__ import annotations

import sys

from backend.config import settings
from backend.services.whisper_service import _model_download_dir, _resolve_model_source


def main() -> int:
    try:
        from faster_whisper import WhisperModel

        model_dir = _model_download_dir()
        model_dir.mkdir(parents=True, exist_ok=True)
        model_source = _resolve_model_source()
        WhisperModel(
            model_source,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
            download_root=str(model_dir),
        )
    except Exception as exc:
        print(f"Failed to prepare faster-whisper model: {exc}", file=sys.stderr)
        return 1

    print(
        "Prepared faster-whisper model "
        f"{settings.whisper_model} at {_model_download_dir()} "
        f"on {settings.whisper_device}/{settings.whisper_compute_type}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
