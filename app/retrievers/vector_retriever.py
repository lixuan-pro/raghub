import json
from pathlib import Path

import numpy as np

from app.embeddings.local_embedder import DEFAULT_MODEL_NAME, embed_texts


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_CHUNKS_PATH = PROJECT_ROOT / "data" / "processed" / "chunks_preview.jsonl"
DEFAULT_EMBEDDINGS_PATH = PROJECT_ROOT / "data" / "processed" / "chunk_embeddings.npy"


def load_jsonl_chunks(chunks_path: Path) -> list[dict]:
    if not chunks_path.exists():
        raise FileNotFoundError(f"Chunks file not found: {chunks_path}")

    chunks: list[dict] = []

    with chunks_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))

    return chunks


def load_chunk_store(
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    embeddings_path: Path = DEFAULT_EMBEDDINGS_PATH,
) -> tuple[list[dict], np.ndarray]:
    chunks = load_jsonl_chunks(chunks_path)

    if not embeddings_path.exists():
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")

    embeddings = np.load(embeddings_path)

    if len(chunks) != embeddings.shape[0]:
        raise ValueError(
            f"Chunks and embeddings count mismatch: "
            f"{len(chunks)} chunks vs {embeddings.shape[0]} embeddings"
        )

    return chunks, embeddings


def cosine_similarity(query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
    query_vec = np.asarray(query_vec, dtype=np.float32)
    doc_vecs = np.asarray(doc_vecs, dtype=np.float32)

    query_norm = np.linalg.norm(query_vec)
    doc_norms = np.linalg.norm(doc_vecs, axis=1)

    if query_norm == 0:
        raise ValueError("query_vec must not be zero vector")

    safe_doc_norms = np.where(doc_norms == 0, 1e-12, doc_norms)

    return (doc_vecs @ query_vec) / (safe_doc_norms * query_norm)


def search_top_k(
    query: str,
    top_k: int = 3,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    embeddings_path: Path = DEFAULT_EMBEDDINGS_PATH,
    model_name: str = DEFAULT_MODEL_NAME,
) -> list[dict]:
    if not query or not query.strip():
        raise ValueError("query must not be empty")

    chunks, embeddings = load_chunk_store(chunks_path, embeddings_path)

    query_embedding = embed_texts([query], model_name=model_name)[0]
    scores = cosine_similarity(query_embedding, embeddings)

    k = min(top_k, len(chunks))
    top_indices = np.argsort(scores)[::-1][:k]

    results: list[dict] = []

    for index in top_indices:
        chunk = chunks[int(index)]

        results.append(
            {
                "chunk_id": int(index),
                "score": float(scores[int(index)]),
                "content": chunk.get("content", ""),
                "source": chunk.get("source"),
                "file_type": chunk.get("file_type"),
                "page": chunk.get("page"),
            }
        )

    return results


class VectorRetriever:
    def __init__(
        self,
        chunks_path: Path = DEFAULT_CHUNKS_PATH,
        embeddings_path: Path = DEFAULT_EMBEDDINGS_PATH,
        model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:
        self.chunks_path = chunks_path
        self.embeddings_path = embeddings_path
        self.model_name = model_name

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        results = search_top_k(
            query=query,
            top_k=top_k,
            chunks_path=self.chunks_path,
            embeddings_path=self.embeddings_path,
            model_name=self.model_name,
        )

        for item in results:
            score = float(item.get("score") or 0)
            item["retrieval_score_detail"] = {
                "vector_score": score,
            }

        return results
