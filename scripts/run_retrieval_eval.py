import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.retrievers.bm25_retriever import BM25Retriever
from app.retrievers.faiss_retriever import FAISSRetriever
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
    resolve_project_path,
)


QUERIES_PATH = PROJECT_ROOT / "eval" / "queries.jsonl"
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
    source_group_lookup: dict[str, set[str]],
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
        "category": item.get("category", "uncategorized"),
        "difficulty": item.get("difficulty", "unknown"),
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


def build_metric_summary(
    results: list[dict[str, Any]],
    top_k: int = TOP_K,
) -> dict[str, Any]:
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
    in_corpus_count = sum(1 for item in results if item.get("case_type", "in_corpus") == "in_corpus")
    out_of_corpus_count = sum(1 for item in results if item.get("case_type") == "out_of_corpus")

    return {
        "total": len(results),
        "total_queries": len(results),
        "in_corpus_count": in_corpus_count,
        "out_of_corpus_count": out_of_corpus_count,
        "top_k": top_k,
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


def build_breakdown(
    results: list[dict[str, Any]],
    field: str,
    top_k: int = TOP_K,
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in results:
        value = str(item.get(field) or "unknown")
        grouped.setdefault(value, []).append(item)
    return {
        value: build_metric_summary(items, top_k=top_k)
        for value, items in sorted(grouped.items())
    }


def build_summary(
    results: list[dict[str, Any]],
    top_k: int = TOP_K,
) -> dict[str, Any]:
    summary = build_metric_summary(results, top_k=top_k)
    summary["category_breakdown"] = build_breakdown(results, "category", top_k=top_k)
    summary["difficulty_breakdown"] = build_breakdown(results, "difficulty", top_k=top_k)
    return summary


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


def build_retrievers(
    queries: list[dict[str, Any]],
    top_k: int = TOP_K,
) -> dict[str, Any]:
    query_texts = [item["query"] for item in queries]
    vector_retriever = VectorRetriever()
    faiss_retriever = FAISSRetriever()
    bm25_retriever = BM25Retriever()
    vector_results_by_query = {
        query: vector_retriever.search(
            query=query,
            top_k=max(top_k, DEFAULT_VECTOR_TOP_N),
        )
        for query in query_texts
    }
    faiss_results_by_query = {
        query: faiss_retriever.search(
            query=query,
            top_k=top_k,
        )
        for query in query_texts
    }
    bm25_results_by_query = {
        query: bm25_retriever.search(
            query=query,
            top_k=max(top_k, DEFAULT_BM25_TOP_N),
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
        "faiss": CachedRetriever(faiss_results_by_query),
    }


def run_retrieval_eval(
    queries_path: Path = QUERIES_PATH,
    output_path: Path = OUTPUT_PATH,
    top_k: int = TOP_K,
) -> dict[str, Any]:
    queries = load_eval_queries(queries_path)
    output_path = resolve_project_path(output_path)
    source_group_lookup = build_source_group_lookup(queries)
    report: dict[str, Any] = {
        "summary": {},
        "results": {},
    }

    for mode, retriever in build_retrievers(queries, top_k=top_k).items():
        mode_results = []
        for item in queries:
            retrieved_chunks = retriever.search(query=item["query"], top_k=top_k)
            mode_results.append(
                evaluate_retrieval_query(
                    item=item,
                    retrieved_chunks=retrieved_chunks,
                    source_group_lookup=source_group_lookup,
                )
            )

        report["summary"][mode] = build_summary(mode_results, top_k=top_k)
        report["results"][mode] = mode_results

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return report


def print_summary(report: dict[str, Any], output_path: Path) -> None:
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
    print(f"output: {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run RAGHub retrieval-only comparison."
    )
    parser.add_argument("--queries", type=Path, default=QUERIES_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--top-k", type=int, default=TOP_K)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = resolve_project_path(args.output)
    report = run_retrieval_eval(
        queries_path=args.queries,
        output_path=output_path,
        top_k=args.top_k,
    )
    print_summary(report, output_path=output_path)


if __name__ == "__main__":
    main()
