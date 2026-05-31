"""真实 embedding 服务。

这里有两个真实向量来源：

1. `EMBEDDING_PROVIDER=openai`
   调用 OpenAI-compatible `/v1/embeddings` API。

2. `EMBEDDING_PROVIDER=local`
   用 fastembed 加载本地真实 embedding 模型。

这两条路都是真实模型推理，不会生成 hash、随机数、固定数组这类假向量。
测试可以 monkeypatch `embed_text`。
"""

import math
import os
import shutil

from backend.config import settings


class EmbeddingUnavailableError(RuntimeError):
    """没有配置真实 embedding 能力时抛出。"""


def embed_text(text: str) -> list[float]:
    if settings.embedding_provider == "local":
        return _embed_text_local(text)
    if settings.embedding_provider != "openai":
        raise EmbeddingUnavailableError(
            "EMBEDDING_PROVIDER must be either 'local' or 'openai'"
        )

    if not settings.openai_api_key:
        raise EmbeddingUnavailableError("OPENAI_API_KEY is required for real embeddings")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    response = client.embeddings.create(model=settings.embedding_model, input=text)
    return list(response.data[0].embedding)


def _embed_text_local(text: str) -> list[float]:
    try:
        from fastembed import TextEmbedding
    except Exception as exc:
        raise EmbeddingUnavailableError("fastembed is required for local embeddings") from exc

    try:
        model = TextEmbedding(
            model_name=settings.local_embedding_model,
            cache_dir=str(settings.local_embedding_cache_dir),
        )
    except Exception:
        # fastembed 某些版本在自定义 cache_dir 下载时会留下不完整目录。
        # 这里仍然调用 fastembed 的真实模型下载和推理，只是先让它用默认缓存成功下载，
        # 再把模型目录复制到项目持久化目录，避免下次重建容器后重新下载。
        model = TextEmbedding(model_name=settings.local_embedding_model)
        _copy_fastembed_default_cache()

    vector = next(model.embed([text]))
    return [float(value) for value in vector.tolist()]


def _copy_fastembed_default_cache() -> None:
    default_cache = "/tmp/fastembed_cache"
    source_root = os.path.join(default_cache)
    if not os.path.exists(source_root):
        return

    os.makedirs(settings.local_embedding_cache_dir, exist_ok=True)
    for name in os.listdir(source_root):
        source = os.path.join(source_root, name)
        target = settings.local_embedding_cache_dir / name
        if os.path.isdir(source) and not target.exists():
            shutil.copytree(source, target)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Embedding dimensions do not match")
    if not a:
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
