import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.retrievers.bm25_retriever import BM25Retriever
from app.retrievers.hybrid_retriever import (
    DEFAULT_BM25_TOP_N,
    DEFAULT_VECTOR_TOP_N,
    HybridRetriever,
)
from app.retrievers.vector_retriever import VectorRetriever
from scripts.run_eval import (
    build_source_group_lookup,
    first_source_hit_rank,
    get_expected_sources,
    is_acceptable_source_hit,
    is_source_group_hit,
    is_source_hit,
    load_eval_queries,
    match_keywords,
    reciprocal_rank,
)


OUTPUT_PATH = PROJECT_ROOT / "eval" / "retrieval_comparison.json"
TOP_K = 3


class CachedRetriever:
    def __init__(self, results_by_query: dict[str, list[dict[str, Any]]]) -> None:
        self.results_by_query = results_by_query

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        return [
            dict(item)
            for item in self.results_by_query.get(query, [])[:top_k]
        ]


def evaluate_retrieval_query(
    item: dict[str, Any],
    retrieved_chunks: list[dict[str, Any]],
    source_group_lookup: dict[str, str],
) -> dict[str, Any]:
    expected_keywords = item.get("expected_keywords", [])
    expected_source = item.get("expected_source")
    expected_sources = get_expected_sources(item)
    expected_source_group = item.get("expected_source_group")
    source_hit_rank = first_source_hit_rank(
        expected_sources=expected_sources,
        retrieved_chunks=retrieved_chunks,
    )
    matched_keywords = match_keywords(
        expected_keywords=expected_keywords,
        answer="",
        retrieved_chunks=retrieved_chunks,
    )

    return {
        "id": item["id"],
        "query": item["query"],
        "case_type": item.get("case_type", "in_corpus"),
        "expected_answerable": item.get("expected_answerable"),
        "expected_source": expected_source,
        "expected_sources": expected_sources,
        "expected_source_group": expected_source_group,
        "retrieved_chunks": retrieved_chunks,
        "top_sources": [
            chunk.get("source") or ""
            for chunk in retrieved_chunks
        ],
        "matched_keywords": matched_keywords,
        "expected_keywords": expected_keywords,
        "keyword_hit_count": len(matched_keywords),
        "source_evaluable": bool(expected_source),
        "acceptable_source_evaluable": bool(expected_sources),
        "source_group_evaluable": bool(expected_source_group),
        "exact_source_hit": is_source_hit(expected_source, retrieved_chunks),
        "acceptable_source_hit": is_acceptable_source_hit(
            expected_sources=expected_sources,
            retrieved_chunks=retrieved_chunks,
        ),
        "source_group_hit": is_source_group_hit(
            expected_source_group=expected_source_group,
            retrieved_chunks=retrieved_chunks,
            source_group_lookup=source_group_lookup,
        ),
        "source_hit_rank": source_hit_rank,
        "mrr_at_k": reciprocal_rank(source_hit_rank),
        "recall_at_k": 1 if source_hit_rank else 0,
    }


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    source_evaluable = [item for item in results if item["source_evaluable"]]
    acceptable_source_evaluable = [
        item for item in results if item["acceptable_source_evaluable"]
    ]
    source_group_evaluable = [
        item for item in results if item["source_group_evaluable"]
    ]
    keyword_evaluable = [
        item
        for item in results
        if item.get("expected_answerable") is not False
    ]

    exact_source_hits = sum(
        1 for item in source_evaluable if item["exact_source_hit"]
    )
    acceptable_source_hits = sum(
        1 for item in acceptable_source_evaluable if item["acceptable_source_hit"]
    )
    source_group_hits = sum(
        1 for item in source_group_evaluable if item["source_group_hit"]
    )
    keyword_hits = sum(item["keyword_hit_count"] for item in keyword_evaluable)
    expected_keywords = sum(
        len(item["expected_keywords"])
        for item in keyword_evaluable
    )

    return {
        "total": len(results),
        "top_k": TOP_K,
        "exact_source_hits": exact_source_hits,
        "exact_source_evaluable": len(source_evaluable),
        "exact_source_hit_rate": (
            exact_source_hits / len(source_evaluable)
            if source_evaluable
            else 0
        ),
        "acceptable_source_hits": acceptable_source_hits,
        "acceptable_source_evaluable": len(acceptable_source_evaluable),
        "acceptable_source_hit_rate": (
            acceptable_source_hits / len(acceptable_source_evaluable)
            if acceptable_source_evaluable
            else 0
        ),
        "source_group_hits": source_group_hits,
        "source_group_evaluable": len(source_group_evaluable),
        "source_group_hit_rate": (
            source_group_hits / len(source_group_evaluable)
            if source_group_evaluable
            else 0
        ),
        "keyword_hits": keyword_hits,
        "expected_keywords": expected_keywords,
        "keyword_hit_rate": (
            keyword_hits / expected_keywords
            if expected_keywords
            else 0
        ),
        "mrr_at_k": (
            sum(float(item["mrr_at_k"]) for item in acceptable_source_evaluable)
            / len(acceptable_source_evaluable)
            if acceptable_source_evaluable
            else 0
        ),
        "recall_at_k": (
            sum(float(item["recall_at_k"]) for item in acceptable_source_evaluable)
            / len(acceptable_source_evaluable)
            if acceptable_source_evaluable
            else 0
        ),
        "top_miss_cases": collect_top_miss_cases(results),
    }


def collect_top_miss_cases(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    misses = [
        item
        for item in results
        if item["source_evaluable"] and not item["exact_source_hit"]
    ]

    return [
        {
            "id": item["id"],
            "query": item["query"],
            "expected_source": item["expected_source"],
            "top_sources": item["top_sources"],
            "acceptable_source_hit": item["acceptable_source_hit"],
            "source_group_hit": item["source_group_hit"],
        }
        for item in misses[:10]
    ]


def build_retrievers(queries: list[dict[str, Any]]) -> dict[str, Any]:
    query_texts = [item["query"] for item in queries]
    vector_retriever = VectorRetriever()
    bm25_retriever = BM25Retriever()
    vector_results_by_query = {
        query: vector_retriever.search(
            query=query,
            top_k=max(TOP_K, DEFAULT_VECTOR_TOP_N),
        )
        for query in query_texts
    }
    bm25_results_by_query = {
        query: bm25_retriever.search(
            query=query,
            top_k=max(TOP_K, DEFAULT_BM25_TOP_N),
        )
        for query in query_texts
    }
    cached_vector_retriever = CachedRetriever(vector_results_by_query)
    cached_bm25_retriever = CachedRetriever(bm25_results_by_query)

    return {
        "vector": CachedRetriever(vector_results_by_query),
        "bm25": CachedRetriever(bm25_results_by_query),
        "hybrid": HybridRetriever(
            vector_retriever=cached_vector_retriever,
            bm25_retriever=cached_bm25_retriever,
            use_rerank=False,
        ),
        "hybrid_rerank": HybridRetriever(
            vector_retriever=cached_vector_retriever,
            bm25_retriever=cached_bm25_retriever,
            use_rerank=True,
        ),
    }


def run_retrieval_eval() -> dict[str, Any]:
    queries = load_eval_queries()
    source_group_lookup = build_source_group_lookup(queries)
    report: dict[str, Any] = {
        "summary": {},
        "results": {},
    }

    for mode, retriever in build_retrievers(queries).items():
        mode_results = []
        for item in queries:
            retrieved_chunks = retriever.search(query=item["query"], top_k=TOP_K)
            mode_results.append(
                evaluate_retrieval_query(
                    item=item,
                    retrieved_chunks=retrieved_chunks,
                    source_group_lookup=source_group_lookup,
                )
            )

        report["summary"][mode] = build_summary(mode_results)
        report["results"][mode] = mode_results

    OUTPUT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return report


def print_summary(report: dict[str, Any]) -> None:
    print("RAGHub retrieval comparison")
    print(
        "mode\texact_source_hit_rate\tacceptable_source_hit_rate\t"
        "source_group_hit_rate\tkeyword_hit_rate\tMRR@k\tRecall@k"
    )
    for mode, summary in report["summary"].items():
        print(
            f"{mode}\t"
            f"{summary['exact_source_hit_rate']:.2f}\t"
            f"{summary['acceptable_source_hit_rate']:.2f}\t"
            f"{summary['source_group_hit_rate']:.2f}\t"
            f"{summary['keyword_hit_rate']:.2f}\t"
            f"{summary['mrr_at_k']:.2f}\t"
            f"{summary['recall_at_k']:.2f}"
        )
    print(f"output: {OUTPUT_PATH}")


def main() -> None:
    report = run_retrieval_eval()
    print_summary(report)


if __name__ == "__main__":
    main()
