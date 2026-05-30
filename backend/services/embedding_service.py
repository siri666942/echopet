"""真实 embedding 服务。

生产逻辑只调用 OpenAI-compatible embeddings API，不生成假向量。
测试可以 monkeypatch `embed_text`。
"""

import math

from backend.config import settings


class EmbeddingUnavailableError(RuntimeError):
    """没有配置真实 embedding 能力时抛出。"""


def embed_text(text: str) -> list[float]:
    if not settings.openai_api_key:
        raise EmbeddingUnavailableError("OPENAI_API_KEY is required for real embeddings")

    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url)
    response = client.embeddings.create(model=settings.embedding_model, input=text)
    return list(response.data[0].embedding)


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
