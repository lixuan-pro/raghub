import json
import sys
from pathlib import Path

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.embeddings.local_embedder import DEFAULT_MODEL_NAME, embed_texts


INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "chunks_preview.jsonl"
OUTPUT_EMBEDDINGS_PATH = PROJECT_ROOT / "data" / "processed" / "chunk_embeddings.npy"
OUTPUT_META_PATH = PROJECT_ROOT / "data" / "processed" / "chunk_embeddings_meta.json"


def load_chunks(jsonl_path: Path) -> list[dict]:
    if not jsonl_path.exists():
        raise FileNotFoundError(f"Input file not found: {jsonl_path}")

    chunks: list[dict] = []

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            chunks.append(json.loads(line))

    return chunks


def main() -> None:
    chunks = load_chunks(INPUT_PATH)

    texts = [
        chunk["content"]
        for chunk in chunks
        if chunk.get("content") and chunk["content"].strip()
    ]

    if not texts:
        raise ValueError("No valid chunk content found.")

    embeddings = embed_texts(texts, model_name=DEFAULT_MODEL_NAME)

    OUTPUT_EMBEDDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    np.save(OUTPUT_EMBEDDINGS_PATH, embeddings)

    meta = {
        "model_name": DEFAULT_MODEL_NAME,
        "num_chunks": len(texts),
        "embedding_dim": int(embeddings.shape[1]),
        "normalized": True,
        "input_path": str(INPUT_PATH.relative_to(PROJECT_ROOT)),
        "output_path": str(OUTPUT_EMBEDDINGS_PATH.relative_to(PROJECT_ROOT)),
    }

    with OUTPUT_META_PATH.open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"chunks: {len(texts)}")
    print(f"embedding shape: {embeddings.shape}")
    print(f"model: {DEFAULT_MODEL_NAME}")
    print(f"output: {OUTPUT_EMBEDDINGS_PATH.relative_to(PROJECT_ROOT)}")
    print(f"meta: {OUTPUT_META_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()