"""测试 embedding 工具函数。"""

import pytest

from backend.services.embedding_service import cosine_similarity


def test_cosine_similarity_normal_vectors():
    assert cosine_similarity([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)


def test_cosine_similarity_zero_vector():
    assert cosine_similarity([0, 0], [1, 0]) == 0.0


def test_cosine_similarity_dimension_mismatch():
    with pytest.raises(ValueError):
        cosine_similarity([1], [1, 2])
