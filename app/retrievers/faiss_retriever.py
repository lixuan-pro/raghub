import json
from pathlib import Path
from typing import Any

import numpy as np

from app.embeddings.local_embedder import DEFAULT_MODEL_NAME, embed_texts
from app.retrievers.vector_retriever import DEFAULT_CHUNKS_PATH, load_jsonl_chunks


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_FAISS_INDEX_PATH = PROJECT_ROOT / "data" / "processed" / "faiss.index"
DEFAULT_FAISS_META_PATH = PROJECT_ROOT / "data" / "processed" / "faiss_meta.json"


def _import_faiss():
    try:
        import faiss
    except ImportError as exc:
        raise ImportError(
            "faiss-cpu is required for the FAISS retriever. "
            "Install dependencies with `pip install -r requirements.txt`."
        ) from exc

    return faiss


def load_faiss_index(index_path: Path = DEFAULT_FAISS_INDEX_PATH):
    if not index_path.exists():
        raise FileNotFoundError(
            f"FAISS index file not found: {index_path}. "
            "Run `python scripts/build_faiss_index.py` first."
        )

    faiss = _import_faiss()
    return faiss.read_index(str(index_path))


def load_faiss_meta(meta_path: Path = DEFAULT_FAISS_META_PATH) -> dict[str, Any]:
    if not meta_path.exists():
        return {}

    with meta_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _validate_top_k(top_k: int) -> None:
    if not isinstance(top_k, int):
        raise ValueError("top_k must be an integer")
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")


def _score_from_faiss_distance(raw_score: float, index_type: str | None) -> float:
    if index_type == "IndexFlatL2":
        return -raw_score
    return raw_score


class FAISSRetriever:
    def __init__(
        self,
        chunks_path: Path = DEFAULT_CHUNKS_PATH,
        index_path: Path = DEFAULT_FAISS_INDEX_PATH,
        meta_path: Path = DEFAULT_FAISS_META_PATH,
        model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:
        self.chunks_path = chunks_path
        self.index_path = index_path
        self.meta_path = meta_path
        self.model_name = model_name
        self._store: tuple[list[dict], Any, dict[str, Any]] | None = None

    def _load_store(self) -> tuple[list[dict], Any, dict[str, Any]]:
        if self._store is not None:
            return self._store

        chunks = load_jsonl_chunks(self.chunks_path)
        if not chunks:
            raise ValueError(f"Chunks file is empty: {self.chunks_path}")

        index = load_faiss_index(self.index_path)
        meta = load_faiss_meta(self.meta_path)

        if index.ntotal != len(chunks):
            raise ValueError(
                f"FAISS index and chunks count mismatch: "
                f"{index.ntotal} vectors vs {len(chunks)} chunks"
            )

        if index.d <= 0:
            raise ValueError(f"Invalid FAISS index dimension: {index.d}")

        meta_dimension = meta.get("dimension")
        if meta_dimension is not None and int(meta_dimension) != int(index.d):
            raise ValueError(
                f"FAISS meta and index dimension mismatch: "
                f"{meta_dimension} meta vs {index.d} index"
            )

        self._store = (chunks, index, meta)
        return self._store

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        _validate_top_k(top_k)

        chunks, index, meta = self._load_store()
        query_embedding = embed_texts([query], model_name=self.model_name)[0]
        query_matrix = np.ascontiguousarray(
            np.asarray([query_embedding], dtype=np.float32)
        )

        if query_matrix.shape[1] != index.d:
            raise ValueError(
                f"Query embedding dimension mismatch: "
                f"{query_matrix.shape[1]} query vs {index.d} index"
            )

        k = min(top_k, len(chunks))
        raw_scores, raw_indices = index.search(query_matrix, k)
        index_type = meta.get("index_type")

        candidates: list[tuple[int, float, float]] = []
        for raw_score, raw_index in zip(raw_scores[0], raw_indices[0]):
            chunk_index = int(raw_index)
            if chunk_index < 0:
                continue

            faiss_distance = float(raw_score)
            score = _score_from_faiss_distance(faiss_distance, index_type)
            candidates.append((chunk_index, score, faiss_distance))

        ranked = sorted(
            candidates,
            key=lambda item: (-item[1], item[0]),
        )

        results: list[dict] = []
        for chunk_index, score, faiss_distance in ranked:
            chunk = chunks[chunk_index]
            results.append(
                {
                    "chunk_id": int(chunk_index),
                    "score": float(score),
                    "content": chunk.get("content", ""),
                    "source": chunk.get("source"),
                    "file_type": chunk.get("file_type"),
                    "page": chunk.get("page"),
                    "retrieval_score_detail": {
                        "faiss_score": float(score),
                        "faiss_distance": float(faiss_distance),
                        "faiss_index_type": index_type or "unknown",
                    },
                }
            )

        return results
