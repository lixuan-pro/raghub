import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.services.rag_service import generate_chat_response


QUERIES_PATH = PROJECT_ROOT / "eval" / "queries.jsonl"
RESULTS_PATH = PROJECT_ROOT / "eval" / "results.json"


def load_eval_queries(path: Path = QUERIES_PATH) -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            queries.append(json.loads(line))

    return queries


def match_keywords(
    expected_keywords: list[str],
    answer: str,
    retrieved_chunks: list[dict[str, Any]],
) -> list[str]:
    haystack_parts = [answer]
    haystack_parts.extend(chunk.get("content") or "" for chunk in retrieved_chunks)
    haystack = "\n".join(haystack_parts).lower()

    return [
        keyword
        for keyword in expected_keywords
        if keyword.lower() in haystack
    ]


def evaluate_query(item: dict[str, Any], top_k: int = 3) -> dict[str, Any]:
    response = generate_chat_response(query=item["query"], top_k=top_k)
    retrieved_chunks = response["retrieved_chunks"]
    expected_keywords = item.get("expected_keywords", [])
    expected_source = item.get("expected_source")

    top_score = retrieved_chunks[0]["score"] if retrieved_chunks else None
    matched_keywords = match_keywords(
        expected_keywords=expected_keywords,
        answer=response["answer"],
        retrieved_chunks=retrieved_chunks,
    )
    source_hit = any(
        chunk.get("source") == expected_source
        for chunk in retrieved_chunks
    )

    return {
        "id": item["id"],
        "query": item["query"],
        "case_type": item.get("case_type", "in_corpus"),
        "note": item.get("note", ""),
        "answer": response["answer"],
        "retrieved_chunks": retrieved_chunks,
        "top_score": top_score,
        "matched_keywords": matched_keywords,
        "expected_keywords": expected_keywords,
        "keyword_hit_count": len(matched_keywords),
        "expected_source": expected_source,
        "source_hit": source_hit,
    }


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    source_hits = sum(1 for item in results if item["source_hit"])
    total_keyword_hits = sum(item["keyword_hit_count"] for item in results)
    total_expected_keywords = sum(len(item["expected_keywords"]) for item in results)

    return {
        "total": len(results),
        "source_hits": source_hits,
        "source_hit_rate": source_hits / len(results) if results else 0,
        "keyword_hits": total_keyword_hits,
        "expected_keywords": total_expected_keywords,
        "keyword_hit_rate": (
            total_keyword_hits / total_expected_keywords
            if total_expected_keywords
            else 0
        ),
    }


def group_results_by_case_type(
    results: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    grouped = {
        "in_corpus": [],
        "boundary_case": [],
    }

    for item in results:
        case_type = item.get("case_type", "in_corpus")
        grouped.setdefault(case_type, []).append(item)

    return grouped


def run_eval() -> dict[str, Any]:
    queries = load_eval_queries()
    results = [evaluate_query(item) for item in queries]
    grouped_results = group_results_by_case_type(results)

    report = {
        "summary": {
            "all_cases": build_summary(results),
            "in_corpus": build_summary(grouped_results.get("in_corpus", [])),
            "boundary_case": build_summary(grouped_results.get("boundary_case", [])),
            "boundary_case_notes": sorted(
                {
                    item["note"]
                    for item in grouped_results.get("boundary_case", [])
                    if item.get("note")
                }
            ),
        },
        "results": results,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return report


def main() -> None:
    report = run_eval()
    summary = report["summary"]
    all_cases = summary["all_cases"]
    in_corpus = summary["in_corpus"]
    boundary_case = summary["boundary_case"]

    print("RAGHub eval summary")
    print(f"total: {all_cases['total']}")
    print(f"all_source_hits: {all_cases['source_hits']}/{all_cases['total']}")
    print(f"all_source_hit_rate: {all_cases['source_hit_rate']:.2f}")
    print(
        "all_keyword_hits: "
        f"{all_cases['keyword_hits']}/{all_cases['expected_keywords']}"
    )
    print(f"all_keyword_hit_rate: {all_cases['keyword_hit_rate']:.2f}")
    print(f"in_corpus_total: {in_corpus['total']}")
    print(
        "in_corpus_source_hits: "
        f"{in_corpus['source_hits']}/{in_corpus['total']}"
    )
    print(
        "in_corpus_keyword_hits: "
        f"{in_corpus['keyword_hits']}/{in_corpus['expected_keywords']}"
    )
    print(f"boundary_case_total: {boundary_case['total']}")
    print(
        "boundary_case_source_hits: "
        f"{boundary_case['source_hits']}/{boundary_case['total']}"
    )
    print("boundary_case_notes:")
    for note in summary["boundary_case_notes"]:
        print(f"- {note}")
    print(f"output: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
