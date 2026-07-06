import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.retrievers.faiss_retriever import (  # noqa: E402
    DEFAULT_FAISS_INDEX_PATH,
    DEFAULT_FAISS_META_PATH,
    _import_faiss,
)
from app.retrievers.vector_retriever import (  # noqa: E402
    DEFAULT_CHUNKS_PATH,
    DEFAULT_EMBEDDINGS_PATH,
    load_jsonl_chunks,
)


DEFAULT_EMBEDDING_META_PATH = (
    PROJECT_ROOT / "data" / "processed" / "chunk_embeddings_meta.json"
)


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def load_embedding_meta(meta_path: Path = DEFAULT_EMBEDDING_META_PATH) -> dict[str, Any]:
    if not meta_path.exists():
        raise FileNotFoundError(f"Embedding meta file not found: {meta_path}")

    with meta_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_valid_embeddings(embeddings_path: Path) -> np.ndarray:
    if not embeddings_path.exists():
        raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")

    embeddings = np.load(embeddings_path)
    if embeddings.ndim != 2:
        raise ValueError(
            f"Embeddings must be a 2D matrix, got shape {embeddings.shape}"
        )
    if embeddings.shape[0] == 0:
        raise ValueError("Embeddings matrix must not be empty")
    if embeddings.shape[1] == 0:
        raise ValueError("Embedding dimension must be greater than 0")

    return np.ascontiguousarray(embeddings.astype("float32", copy=False))


def resolve_index_type(normalized: Any) -> str:
    if normalized is True:
        return "IndexFlatIP"
    if normalized is False:
        return "IndexFlatL2"
    raise ValueError(
        "Embedding meta must contain boolean field `normalized` "
        "before choosing a FAISS index type."
    )


def build_faiss_index(
    embeddings_path: Path = DEFAULT_EMBEDDINGS_PATH,
    chunks_path: Path = DEFAULT_CHUNKS_PATH,
    embedding_meta_path: Path = DEFAULT_EMBEDDING_META_PATH,
    index_path: Path = DEFAULT_FAISS_INDEX_PATH,
    faiss_meta_path: Path = DEFAULT_FAISS_META_PATH,
) -> dict[str, Any]:
    chunks = load_jsonl_chunks(chunks_path)
    if not chunks:
        raise ValueError(f"Chunks file is empty: {chunks_path}")

    embeddings = load_valid_embeddings(embeddings_path)
    if len(chunks) != embeddings.shape[0]:
        raise ValueError(
            f"Chunks and embeddings count mismatch: "
            f"{len(chunks)} chunks vs {embeddings.shape[0]} embeddings"
        )

    embedding_meta = load_embedding_meta(embedding_meta_path)
    meta_num_chunks = embedding_meta.get("num_chunks")
    if meta_num_chunks is not None and int(meta_num_chunks) != int(embeddings.shape[0]):
        raise ValueError(
            f"Embedding meta and matrix count mismatch: "
            f"{meta_num_chunks} meta vs {embeddings.shape[0]} embeddings"
        )

    meta_dimension = embedding_meta.get("embedding_dim")
    if meta_dimension is not None and int(meta_dimension) != int(embeddings.shape[1]):
        raise ValueError(
            f"Embedding meta and matrix dimension mismatch: "
            f"{meta_dimension} meta vs {embeddings.shape[1]} embeddings"
        )

    index_type = resolve_index_type(embedding_meta.get("normalized"))
    dimension = int(embeddings.shape[1])

    faiss = _import_faiss()
    if index_type == "IndexFlatIP":
        index = faiss.IndexFlatIP(dimension)
    else:
        index = faiss.IndexFlatL2(dimension)

    index.add(embeddings)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_path))

    meta = {
        "embedding_path": _relative(embeddings_path),
        "chunks_path": _relative(chunks_path),
        "embedding_meta_path": _relative(embedding_meta_path),
        "index_path": _relative(index_path),
        "num_vectors": int(index.ntotal),
        "dimension": dimension,
        "index_type": index_type,
        "normalized": bool(embedding_meta["normalized"]),
        "model_name": embedding_meta.get("model_name"),
    }

    faiss_meta_path.parent.mkdir(parents=True, exist_ok=True)
    with faiss_meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


def main() -> None:
    meta = build_faiss_index()

    print("FAISS index built")
    print(f"vectors: {meta['num_vectors']}")
    print(f"dimension: {meta['dimension']}")
    print(f"index_type: {meta['index_type']}")
    print(f"normalized: {meta['normalized']}")
    print(f"index: {meta['index_path']}")
    print(f"meta: {DEFAULT_FAISS_META_PATH.relative_to(PROJECT_ROOT).as_posix()}")


if __name__ == "__main__":
    main()
