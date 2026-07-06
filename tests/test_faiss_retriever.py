import json
from pathlib import Path

import numpy as np
import pytest

import app.retrievers.faiss_retriever as faiss_retriever
from app.retrievers.faiss_retriever import FAISSRetriever
from app.retrievers.vector_retriever import VectorRetriever
from app.services import retrieve_service
from scripts.build_faiss_index import build_faiss_index


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def make_chunks() -> list[dict]:
    return [
        {
            "content": "RAGHub supports retrieval APIs.",
            "source": "README.md",
            "file_type": "md",
            "page": None,
        },
        {
            "content": "DeepSeek provider configuration.",
            "source": "docs/llm.md",
            "file_type": "md",
            "page": None,
        },
    ]


def build_tiny_faiss_store(tmp_path: Path) -> tuple[Path, Path, Path]:
    chunks_path = tmp_path / "chunks_preview.jsonl"
    embeddings_path = tmp_path / "chunk_embeddings.npy"
    embedding_meta_path = tmp_path / "chunk_embeddings_meta.json"
    index_path = tmp_path / "faiss.index"
    faiss_meta_path = tmp_path / "faiss_meta.json"

    write_jsonl(chunks_path, make_chunks())
    np.save(
        embeddings_path,
        np.array(
            [
                [1.0, 0.0],
                [0.0, 1.0],
            ],
            dtype=np.float32,
        ),
    )
    embedding_meta_path.write_text(
        json.dumps(
            {
                "model_name": "test-model",
                "num_chunks": 2,
                "embedding_dim": 2,
                "normalized": True,
                "input_path": str(chunks_path),
                "output_path": str(embeddings_path),
            }
        ),
        encoding="utf-8",
    )

    build_faiss_index(
        embeddings_path=embeddings_path,
        chunks_path=chunks_path,
        embedding_meta_path=embedding_meta_path,
        index_path=index_path,
        faiss_meta_path=faiss_meta_path,
    )

    return chunks_path, index_path, faiss_meta_path


def test_build_faiss_index_writes_index_and_meta(tmp_path):
    chunks_path, index_path, faiss_meta_path = build_tiny_faiss_store(tmp_path)

    assert chunks_path.exists()
    assert index_path.exists()
    assert faiss_meta_path.exists()

    meta = json.loads(faiss_meta_path.read_text(encoding="utf-8"))
    assert meta["num_vectors"] == 2
    assert meta["dimension"] == 2
    assert meta["index_type"] == "IndexFlatIP"
    assert meta["normalized"] is True


def test_faiss_retriever_loads_index_and_returns_top_k(monkeypatch, tmp_path):
    chunks_path, index_path, faiss_meta_path = build_tiny_faiss_store(tmp_path)

    monkeypatch.setattr(
        faiss_retriever,
        "embed_texts",
        lambda texts, model_name: np.array([[1.0, 0.0]], dtype=np.float32),
    )

    results = FAISSRetriever(
        chunks_path=chunks_path,
        index_path=index_path,
        meta_path=faiss_meta_path,
    ).search(query="RAGHub retrieval", top_k=1)

    assert len(results) == 1
    assert results[0]["chunk_id"] == 0
    assert results[0]["score"] == pytest.approx(1.0)
    for field in ("chunk_id", "score", "content", "source", "file_type", "page"):
        assert field in results[0]
    assert results[0]["retrieval_score_detail"]["faiss_index_type"] == "IndexFlatIP"


def test_faiss_retriever_missing_index_has_actionable_error(tmp_path):
    chunks_path = tmp_path / "chunks_preview.jsonl"
    write_jsonl(chunks_path, make_chunks())

    retriever = FAISSRetriever(
        chunks_path=chunks_path,
        index_path=tmp_path / "missing.index",
        meta_path=tmp_path / "faiss_meta.json",
    )

    with pytest.raises(FileNotFoundError, match="build_faiss_index.py"):
        retriever.search(query="RAGHub", top_k=1)


def test_default_retriever_provider_stays_vector(monkeypatch):
    monkeypatch.delenv("RETRIEVER_PROVIDER", raising=False)

    assert retrieve_service.get_retriever_provider() == "vector"
    assert isinstance(retrieve_service.build_retriever(), VectorRetriever)


def test_faiss_retriever_provider_can_be_selected(monkeypatch):
    monkeypatch.setenv("RETRIEVER_PROVIDER", "faiss")

    assert isinstance(retrieve_service.build_retriever(), FAISSRetriever)
