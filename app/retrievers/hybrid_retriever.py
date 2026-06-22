from pathlib import Path
from typing import Any

from app.retrievers.bm25_retriever import BM25Retriever, tokenize
from app.retrievers.vector_retriever import VectorRetriever


DEFAULT_ALPHA = 0.50
DEFAULT_BETA = 0.40
DEFAULT_GAMMA = 0.10
DEFAULT_VECTOR_TOP_N = 10
DEFAULT_BM25_TOP_N = 10


def normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}

    min_score = min(scores.values())
    max_score = max(scores.values())

    if max_score == min_score:
        return {
            chunk_id: 1.0 if score > 0 else 0.0
            for chunk_id, score in scores.items()
        }

    return {
        chunk_id: (score - min_score) / (max_score - min_score)
        for chunk_id, score in scores.items()
    }


def meaningful_tokens(text: str) -> set[str]:
    tokens = set(tokenize(text))
    return {
        token
        for token in tokens
        if len(token) >= 2 or token.startswith("/") or "_" in token or "." in token
    }


def source_match_score(query: str, item: dict[str, Any]) -> float:
    query_tokens = meaningful_tokens(query)
    if not query_tokens:
        return 0.0

    source = str(item.get("source") or "")
    filename = Path(source).name
    source_tokens = meaningful_tokens(f"{source} {filename}")
    content_tokens = meaningful_tokens(str(item.get("content") or ""))

    source_overlap = len(query_tokens & source_tokens) / len(query_tokens)
    content_overlap = len(query_tokens & content_tokens) / len(query_tokens)

    return min(1.0, source_overlap * 0.7 + content_overlap * 0.3)


def lightweight_rerank_score(query: str, item: dict[str, Any]) -> float:
    query_tokens = meaningful_tokens(query)
    if not query_tokens:
        return 0.0

    content_tokens = meaningful_tokens(str(item.get("content") or ""))
    source_tokens = meaningful_tokens(str(item.get("source") or ""))
    combined_tokens = content_tokens | source_tokens

    overlap = len(query_tokens & combined_tokens) / len(query_tokens)
    source_overlap = len(query_tokens & source_tokens) / len(query_tokens)

    exact_entities = {
        "/retrieve",
        "/chat",
        "chunk_id",
        "score",
        "content",
        "source",
        "file_type",
        "page",
        "api_key",
        "deepseek_api_key",
        ".env",
        "qdrant",
        "milvus",
        "pgvector",
    }
    entity_hits = len((query_tokens & combined_tokens) & exact_entities)
    entity_score = min(entity_hits / 3, 1.0)

    return min(1.0, overlap * 0.5 + source_overlap * 0.3 + entity_score * 0.2)


class HybridRetriever:
    def __init__(
        self,
        vector_retriever: Any | None = None,
        bm25_retriever: Any | None = None,
        vector_top_n: int = DEFAULT_VECTOR_TOP_N,
        bm25_top_n: int = DEFAULT_BM25_TOP_N,
        alpha: float = DEFAULT_ALPHA,
        beta: float = DEFAULT_BETA,
        gamma: float = DEFAULT_GAMMA,
        use_rerank: bool = False,
    ) -> None:
        self.vector_retriever = vector_retriever or VectorRetriever()
        self.bm25_retriever = bm25_retriever or BM25Retriever()
        self.vector_top_n = vector_top_n
        self.bm25_top_n = bm25_top_n
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.use_rerank = use_rerank

    def _merge_candidates(
        self,
        vector_results: list[dict],
        bm25_results: list[dict],
    ) -> dict[str, dict]:
        candidates: dict[str, dict] = {}

        for result in vector_results:
            chunk_id = str(result["chunk_id"])
            item = dict(result)
            item["chunk_id"] = chunk_id
            detail = dict(item.get("retrieval_score_detail") or {})
            detail["vector_score"] = float(result.get("score") or 0)
            item["retrieval_score_detail"] = detail
            candidates[chunk_id] = item

        for result in bm25_results:
            chunk_id = str(result["chunk_id"])
            item = candidates.get(chunk_id, dict(result))
            item["chunk_id"] = chunk_id
            detail = dict(item.get("retrieval_score_detail") or {})
            detail["bm25_score"] = float(result.get("score") or 0)
            item["retrieval_score_detail"] = detail
            candidates[chunk_id] = item

        return candidates

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if not query or not query.strip():
            raise ValueError("query must not be empty")

        vector_results = self.vector_retriever.search(
            query=query,
            top_k=self.vector_top_n,
        )
        bm25_results = self.bm25_retriever.search(
            query=query,
            top_k=self.bm25_top_n,
        )
        candidates = self._merge_candidates(vector_results, bm25_results)

        vector_scores = {
            chunk_id: item.get("retrieval_score_detail", {}).get("vector_score", 0.0)
            for chunk_id, item in candidates.items()
            if "vector_score" in item.get("retrieval_score_detail", {})
        }
        bm25_scores = {
            chunk_id: item.get("retrieval_score_detail", {}).get("bm25_score", 0.0)
            for chunk_id, item in candidates.items()
            if "bm25_score" in item.get("retrieval_score_detail", {})
        }
        normalized_vector_scores = normalize_scores(vector_scores)
        normalized_bm25_scores = normalize_scores(bm25_scores)

        for chunk_id, item in candidates.items():
            vector_score_norm = normalized_vector_scores.get(chunk_id, 0.0)
            bm25_score_norm = normalized_bm25_scores.get(chunk_id, 0.0)
            source_score = source_match_score(query=query, item=item)
            final_score = (
                self.alpha * vector_score_norm
                + self.beta * bm25_score_norm
                + self.gamma * source_score
            )

            rerank_score = 0.0
            if self.use_rerank:
                rerank_score = lightweight_rerank_score(query=query, item=item)
                final_score += 0.15 * rerank_score

            detail = dict(item.get("retrieval_score_detail") or {})
            detail.update(
                {
                    "vector_score": float(detail.get("vector_score", 0.0)),
                    "bm25_score": float(detail.get("bm25_score", 0.0)),
                    "vector_score_norm": vector_score_norm,
                    "bm25_score_norm": bm25_score_norm,
                    "source_match_score": source_score,
                    "rerank_score": rerank_score,
                    "final_score": final_score,
                }
            )
            item["retrieval_score_detail"] = detail
            item["score"] = final_score

        return sorted(
            candidates.values(),
            key=lambda item: item["score"],
            reverse=True,
        )[:top_k]
