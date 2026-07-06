import os

from app.retrievers.bm25_retriever import BM25Retriever
from app.retrievers.faiss_retriever import FAISSRetriever
from app.retrievers.hybrid_retriever import HybridRetriever
from app.retrievers.vector_retriever import VectorRetriever


DEFAULT_RETRIEVER_PROVIDER = "vector"
API_CHUNK_FIELDS = ("chunk_id", "score", "content", "source", "file_type", "page")


def get_retriever_provider() -> str:
    return os.getenv("RETRIEVER_PROVIDER", DEFAULT_RETRIEVER_PROVIDER).lower()


def build_retriever(provider: str | None = None):
    selected_provider = (provider or get_retriever_provider()).lower()

    if selected_provider == "vector":
        return VectorRetriever()
    if selected_provider == "bm25":
        return BM25Retriever()
    if selected_provider == "faiss":
        return FAISSRetriever()
    if selected_provider == "hybrid":
        return HybridRetriever(use_rerank=False)
    if selected_provider == "hybrid_rerank":
        return HybridRetriever(use_rerank=True)

    raise ValueError(f"Unsupported retriever provider: {selected_provider}")


def strip_internal_fields(item: dict) -> dict:
    return {
        "chunk_id": str(item["chunk_id"]),
        "score": float(item["score"]),
        "content": item["content"],
        "source": item.get("source") or "",
        "file_type": item.get("file_type") or "",
        "page": item["page"],
    }


def retrieve_chunks(query: str, top_k: int = 3) -> list[dict]:
    retriever = build_retriever()
    results = retriever.search(query=query, top_k=top_k)

    return [strip_internal_fields(item) for item in results]
