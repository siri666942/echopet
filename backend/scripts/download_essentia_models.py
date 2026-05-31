"""下载 EchoPet 入库需要的 Essentia 官方 TensorFlow 模型。

运行方式：
    docker compose exec echopet-backend python -m backend.scripts.download_essentia_models

为什么需要这个脚本：
    后端要求真实歌曲必须经过 Essentia 分析，不能写假特征。
    `essentia-tensorflow` 只是运行库，不自带所有预训练模型文件。
    所以这里把项目当前需要的 `.pb` 模型下载到 `backend/models/essentia/`。
"""

from __future__ import annotations

import time
import urllib.request
from pathlib import Path

from backend.config import settings


MODEL_URLS = {
    "msd-musicnn-1.pb": "https://essentia.upf.edu/models/autotagging/msd/msd-musicnn-1.pb",
    "discogs-effnet-bs64-1.pb": "https://essentia.upf.edu/models/feature-extractors/discogs-effnet/discogs-effnet-bs64-1.pb",
    "genre_discogs400-discogs-effnet-1.pb": "https://essentia.upf.edu/models/classification-heads/genre_discogs400/genre_discogs400-discogs-effnet-1.pb",
    "moods_mirex-msd-musicnn-1.pb": "https://essentia.upf.edu/models/classification-heads/moods_mirex/moods_mirex-msd-musicnn-1.pb",
    "danceability-msd-musicnn-1.pb": "https://essentia.upf.edu/models/classification-heads/danceability/danceability-msd-musicnn-1.pb",
    "deam-msd-musicnn-2.pb": "https://essentia.upf.edu/models/classification-heads/deam/deam-msd-musicnn-2.pb",
    "voice_instrumental-msd-musicnn-1.pb": "https://essentia.upf.edu/models/classification-heads/voice_instrumental/voice_instrumental-msd-musicnn-1.pb",
    "nsynth_acoustic_electronic-discogs-effnet-1.pb": "https://essentia.upf.edu/models/classification-heads/nsynth_acoustic_electronic/nsynth_acoustic_electronic-discogs-effnet-1.pb",
}


def main() -> None:
    target_dir = Path(settings.essentia_model_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    for filename, url in MODEL_URLS.items():
        target = target_dir / filename
        if target.exists() and target.stat().st_size > 0:
            print(f"EXISTS {target}")
            continue

        print(f"DOWNLOAD {url}")
        _download_with_retries(url, target)
        print(f"SAVED {target}")

    print(f"model_dir={target_dir}")


def _download_with_retries(url: str, target: Path) -> None:
    temp_target = target.with_suffix(target.suffix + ".part")
    last_error: Exception | None = None

    for attempt in range(1, 4):
        try:
            if temp_target.exists():
                temp_target.unlink()
            with urllib.request.urlopen(url, timeout=120) as response:
                expected_size = response.headers.get("Content-Length")
                with temp_target.open("wb") as output:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        output.write(chunk)

            if expected_size and temp_target.stat().st_size != int(expected_size):
                raise RuntimeError(
                    f"incomplete download: got {temp_target.stat().st_size}, expected {expected_size}"
                )

            temp_target.replace(target)
            return
        except Exception as exc:
            last_error = exc
            print(f"RETRY {attempt}/3 failed: {exc}")
            time.sleep(2)

    raise RuntimeError(f"failed to download {url}: {last_error}")


if __name__ == "__main__":
    main()
