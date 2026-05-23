import numpy as np
import pytest

from app.retrievers.vector_retriever import cosine_similarity


def test_cosine_similarity_returns_expected_order():
    query_vec = np.array([1.0, 0.0], dtype=np.float32)

    doc_vecs = np.array(
        [
            [1.0, 0.0],
            [0.0, 1.0],
            [0.8, 0.2],
        ],
        dtype=np.float32,
    )

    scores = cosine_similarity(query_vec, doc_vecs)

    ranked_indices = np.argsort(scores)[::-1].tolist()

    assert ranked_indices[0] == 0
    assert ranked_indices[1] == 2
    assert ranked_indices[2] == 1


def test_cosine_similarity_rejects_zero_query_vector():
    query_vec = np.array([0.0, 0.0], dtype=np.float32)
    doc_vecs = np.array([[1.0, 0.0]], dtype=np.float32)

    with pytest.raises(ValueError):
        cosine_similarity(query_vec, doc_vecs)