import numpy as np
import pytest

import app.retrievers.vector_retriever as vector_retriever
from app.retrievers.vector_retriever import VectorRetriever, cosine_similarity


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


def test_vector_retriever_wrapper_uses_search_top_k(monkeypatch):
    def fake_search_top_k(query: str, top_k: int, **kwargs):
        return [
            {
                "chunk_id": 7,
                "score": 0.42,
                "content": "RAGHub vector result",
                "source": "README.md",
                "file_type": "md",
                "page": None,
            }
        ]

    monkeypatch.setattr(vector_retriever, "search_top_k", fake_search_top_k)

    results = VectorRetriever().search(query="RAGHub", top_k=1)

    assert results[0]["chunk_id"] == 7
    assert results[0]["retrieval_score_detail"]["vector_score"] == 0.42
