import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.services.rag_service import generate_chat_response


QUERIES_PATH = PROJECT_ROOT / "eval" / "queries.jsonl"
RESULTS_PATH = PROJECT_ROOT / "eval" / "results.json"


def resolve_project_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_eval_queries(path: Path = QUERIES_PATH) -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    path = resolve_project_path(path)

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


def is_source_hit(
    expected_source: str | None,
    retrieved_chunks: list[dict[str, Any]],
) -> bool:
    if not expected_source:
        return False

    return any(
        chunk.get("source") == expected_source
        for chunk in retrieved_chunks
    )


def get_expected_sources(item: dict[str, Any]) -> list[str]:
    expected_sources = item.get("expected_sources")
    if isinstance(expected_sources, list):
        return [
            source
            for source in expected_sources
            if isinstance(source, str) and source
        ]

    expected_source = item.get("expected_source")
    if isinstance(expected_source, str) and expected_source:
        return [expected_source]

    return []


def build_source_group_lookup(
    queries: list[dict[str, Any]],
) -> dict[str, set[str]]:
    lookup: dict[str, set[str]] = {}

    for item in queries:
        expected_source_group = item.get("expected_source_group")
        if not expected_source_group:
            continue

        group_sources = lookup.setdefault(expected_source_group, set())
        for source in get_expected_sources(item):
            group_sources.add(source)

    return lookup


def is_acceptable_source_hit(
    expected_sources: list[str],
    retrieved_chunks: list[dict[str, Any]],
) -> bool:
    if not expected_sources:
        return False

    expected_source_set = set(expected_sources)
    return any(
        chunk.get("source") in expected_source_set
        for chunk in retrieved_chunks
    )


def is_source_group_hit(
    expected_source_group: str | None,
    retrieved_chunks: list[dict[str, Any]],
    source_group_lookup: dict[str, set[str]],
) -> bool:
    if not expected_source_group:
        return False

    expected_group_sources = source_group_lookup.get(expected_source_group, set())
    if not expected_group_sources:
        return False

    return any(
        str(chunk.get("source") or "") in expected_group_sources
        for chunk in retrieved_chunks
    )


def first_source_hit_rank(
    expected_sources: list[str],
    retrieved_chunks: list[dict[str, Any]],
) -> int | None:
    if not expected_sources:
        return None

    expected_source_set = set(expected_sources)
    for index, chunk in enumerate(retrieved_chunks, start=1):
        if chunk.get("source") in expected_source_set:
            return index

    return None


def reciprocal_rank(rank: int | None) -> float:
    return 1 / rank if rank else 0.0


def evaluate_query(
    item: dict[str, Any],
    top_k: int = 3,
    source_group_lookup: dict[str, set[str]] | None = None,
) -> dict[str, Any]:
    response = generate_chat_response(query=item["query"], top_k=top_k)
    retrieved_chunks = response["retrieved_chunks"]
    expected_keywords = item.get("expected_keywords", [])
    expected_source = item.get("expected_source")
    expected_sources = get_expected_sources(item)
    expected_source_group = item.get("expected_source_group")
    expected_answerable = item.get("expected_answerable")
    is_answerable = bool(response.get("is_answerable"))
    source_group_lookup = source_group_lookup or build_source_group_lookup([item])

    top_score = retrieved_chunks[0]["score"] if retrieved_chunks else None
    matched_keywords = match_keywords(
        expected_keywords=expected_keywords,
        answer=response["answer"],
        retrieved_chunks=retrieved_chunks,
    )
    source_hit_rank = first_source_hit_rank(
        expected_sources=expected_sources,
        retrieved_chunks=retrieved_chunks,
    )

    return {
        "id": item["id"],
        "query": item["query"],
        "category": item.get("category", "uncategorized"),
        "difficulty": item.get("difficulty", "unknown"),
        "case_type": item.get("case_type", "in_corpus"),
        "note": item.get("note", ""),
        "answer": response["answer"],
        "is_answerable": is_answerable,
        "expected_answerable": expected_answerable,
        "answerable_correct": (
            is_answerable == expected_answerable
            if isinstance(expected_answerable, bool)
            else None
        ),
        "reason": response.get("reason"),
        "retrieved_chunks": retrieved_chunks,
        "top_score": top_score,
        "matched_keywords": matched_keywords,
        "expected_keywords": expected_keywords,
        "keyword_hit_count": len(matched_keywords),
        "expected_source": expected_source,
        "expected_sources": expected_sources,
        "expected_source_group": expected_source_group,
        "source_hit": is_source_hit(expected_source, retrieved_chunks),
        "source_evaluable": bool(expected_source),
        "exact_source_hit": is_source_hit(expected_source, retrieved_chunks),
        "acceptable_source_hit": is_acceptable_source_hit(
            expected_sources=expected_sources,
            retrieved_chunks=retrieved_chunks,
        ),
        "acceptable_source_evaluable": bool(expected_sources),
        "source_group_hit": is_source_group_hit(
            expected_source_group=expected_source_group,
            retrieved_chunks=retrieved_chunks,
            source_group_lookup=source_group_lookup,
        ),
        "source_group_evaluable": bool(expected_source_group),
        "source_hit_rank": source_hit_rank,
        "mrr_at_k": reciprocal_rank(source_hit_rank),
        "recall_at_k": 1 if source_hit_rank else 0,
    }


def build_metric_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    source_evaluable = [item for item in results if item.get("source_evaluable")]
    source_hits = sum(1 for item in source_evaluable if item["source_hit"])
    acceptable_source_evaluable = [
        item for item in results if item.get("acceptable_source_evaluable")
    ]
    acceptable_source_hits = sum(
        1 for item in acceptable_source_evaluable if item["acceptable_source_hit"]
    )
    source_group_evaluable = [
        item for item in results if item.get("source_group_evaluable")
    ]
    source_group_hits = sum(
        1 for item in source_group_evaluable if item["source_group_hit"]
    )
    total_mrr_at_k = sum(
        float(item.get("mrr_at_k") or 0)
        for item in acceptable_source_evaluable
    )
    total_recall_at_k = sum(
        float(item.get("recall_at_k") or 0)
        for item in acceptable_source_evaluable
    )
    keyword_evaluable = [
        item
        for item in results
        if item.get("expected_answerable") is not False
    ]
    total_keyword_hits = sum(item["keyword_hit_count"] for item in keyword_evaluable)
    total_expected_keywords = sum(
        len(item["expected_keywords"]) for item in keyword_evaluable
    )
    answerable_count = sum(1 for item in results if item.get("is_answerable"))

    answerable_evaluable = [
        item for item in results if isinstance(item.get("expected_answerable"), bool)
    ]
    answerable_correct = sum(
        1 for item in answerable_evaluable if item.get("answerable_correct")
    )
    expected_answerable_items = [
        item for item in answerable_evaluable if item["expected_answerable"] is True
    ]
    expected_unanswerable_items = [
        item for item in answerable_evaluable if item["expected_answerable"] is False
    ]
    expected_answerable_accepted = sum(
        1 for item in expected_answerable_items if item.get("is_answerable") is True
    )
    expected_unanswerable_rejected = sum(
        1 for item in expected_unanswerable_items if item.get("is_answerable") is False
    )
    in_corpus_count = sum(1 for item in results if item.get("case_type", "in_corpus") == "in_corpus")
    out_of_corpus_count = sum(1 for item in results if item.get("case_type") == "out_of_corpus")

    return {
        "total": len(results),
        "total_queries": len(results),
        "in_corpus_count": in_corpus_count,
        "out_of_corpus_count": out_of_corpus_count,
        "answerable_count": answerable_count,
        "answerable_total": len(answerable_evaluable),
        "answerable_correct": answerable_correct,
        "answerable_accuracy": (
            answerable_correct / len(answerable_evaluable)
            if answerable_evaluable
            else 0
        ),
        "answerability_accuracy": (
            answerable_correct / len(answerable_evaluable)
            if answerable_evaluable
            else 0
        ),
        "expected_answerable_total": len(expected_answerable_items),
        "expected_answerable_accepted": expected_answerable_accepted,
        "expected_answerable_accept_rate": (
            expected_answerable_accepted / len(expected_answerable_items)
            if expected_answerable_items
            else 0
        ),
        "expected_unanswerable_total": len(expected_unanswerable_items),
        "expected_unanswerable_rejected": expected_unanswerable_rejected,
        "expected_unanswerable_reject_rate": (
            expected_unanswerable_rejected / len(expected_unanswerable_items)
            if expected_unanswerable_items
            else 0
        ),
        "out_of_corpus_rejected": expected_unanswerable_rejected,
        "source_hits": source_hits,
        "source_evaluable": len(source_evaluable),
        "source_hit_rate": (
            source_hits / len(source_evaluable)
            if source_evaluable
            else 0
        ),
        "exact_source_hits": source_hits,
        "exact_source_evaluable": len(source_evaluable),
        "exact_source_hit_rate": (
            source_hits / len(source_evaluable)
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
        "mrr_at_k": (
            total_mrr_at_k / len(acceptable_source_evaluable)
            if acceptable_source_evaluable
            else 0
        ),
        "recall_at_k": (
            total_recall_at_k / len(acceptable_source_evaluable)
            if acceptable_source_evaluable
            else 0
        ),
        "keyword_hits": total_keyword_hits,
        "expected_keywords": total_expected_keywords,
        "keyword_hit_rate": (
            total_keyword_hits / total_expected_keywords
            if total_expected_keywords
            else 0
        ),
    }


def build_breakdown(
    results: list[dict[str, Any]],
    field: str,
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in results:
        value = str(item.get(field) or "unknown")
        grouped.setdefault(value, []).append(item)
    return {
        value: build_metric_summary(items)
        for value, items in sorted(grouped.items())
    }


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    summary = build_metric_summary(results)
    summary["category_breakdown"] = build_breakdown(results, "category")
    summary["difficulty_breakdown"] = build_breakdown(results, "difficulty")
    return summary


def group_results_by_case_type(
    results: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}

    for item in results:
        case_type = item.get("case_type", "in_corpus")
        grouped.setdefault(case_type, []).append(item)

    return grouped


def collect_case_notes(results: list[dict[str, Any]]) -> dict[str, list[str]]:
    grouped = group_results_by_case_type(results)
    notes: dict[str, list[str]] = {}

    for case_type, items in grouped.items():
        notes[case_type] = sorted(
            {
                item["note"]
                for item in items
                if item.get("note")
            }
        )

    return notes


def run_eval(
    queries_path: Path = QUERIES_PATH,
    output_path: Path = RESULTS_PATH,
    top_k: int = 3,
) -> dict[str, Any]:
    queries = load_eval_queries(queries_path)
    output_path = resolve_project_path(output_path)
    source_group_lookup = build_source_group_lookup(queries)
    results = [
        evaluate_query(
            item,
            top_k=top_k,
            source_group_lookup=source_group_lookup,
        )
        for item in queries
    ]
    grouped_results = group_results_by_case_type(results)

    case_type_summaries = {
        case_type: build_summary(items)
        for case_type, items in sorted(grouped_results.items())
    }

    report = {
        "summary": {
            "all_cases": build_summary(results),
            "case_types": case_type_summaries,
            "case_type_notes": collect_case_notes(results),
        },
        "results": results,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return report


def print_summary_line(prefix: str, summary: dict[str, Any]) -> None:
    print(f"{prefix}_total: {summary['total']}")
    print(f"{prefix}_total_queries: {summary['total_queries']}")
    print(f"{prefix}_in_corpus_count: {summary['in_corpus_count']}")
    print(f"{prefix}_out_of_corpus_count: {summary['out_of_corpus_count']}")
    print(f"{prefix}_answerable: {summary['answerable_count']}/{summary['total']}")
    print(
        f"{prefix}_answerable_correct: "
        f"{summary['answerable_correct']}/{summary['answerable_total']}"
    )
    print(f"{prefix}_answerable_accuracy: {summary['answerable_accuracy']:.2f}")
    print(
        f"{prefix}_expected_answerable_accepted: "
        f"{summary['expected_answerable_accepted']}/"
        f"{summary['expected_answerable_total']}"
    )
    print(
        f"{prefix}_expected_answerable_accept_rate: "
        f"{summary['expected_answerable_accept_rate']:.2f}"
    )
    print(
        f"{prefix}_expected_unanswerable_rejected: "
        f"{summary['expected_unanswerable_rejected']}/"
        f"{summary['expected_unanswerable_total']}"
    )
    print(
        f"{prefix}_expected_unanswerable_reject_rate: "
        f"{summary['expected_unanswerable_reject_rate']:.2f}"
    )
    print(
        f"{prefix}_source_hits: "
        f"{summary['source_hits']}/{summary['source_evaluable']}"
    )
    print(f"{prefix}_source_hit_rate: {summary['source_hit_rate']:.2f}")
    print(
        f"{prefix}_acceptable_source_hits: "
        f"{summary['acceptable_source_hits']}/"
        f"{summary['acceptable_source_evaluable']}"
    )
    print(
        f"{prefix}_acceptable_source_hit_rate: "
        f"{summary['acceptable_source_hit_rate']:.2f}"
    )
    print(
        f"{prefix}_source_group_hits: "
        f"{summary['source_group_hits']}/"
        f"{summary['source_group_evaluable']}"
    )
    print(
        f"{prefix}_source_group_hit_rate: "
        f"{summary['source_group_hit_rate']:.2f}"
    )
    print(f"{prefix}_mrr_at_k: {summary['mrr_at_k']:.2f}")
    print(f"{prefix}_recall_at_k: {summary['recall_at_k']:.2f}")
    print(
        f"{prefix}_keyword_hits: "
        f"{summary['keyword_hits']}/{summary['expected_keywords']}"
    )
    print(f"{prefix}_keyword_hit_rate: {summary['keyword_hit_rate']:.2f}")


def print_breakdown(title: str, breakdown: dict[str, dict[str, Any]]) -> None:
    print(f"{title}:")
    for key, summary in breakdown.items():
        print(
            f"- {key}: total={summary['total_queries']}, "
            f"exact={summary['exact_source_hit_rate']:.2f}, "
            f"acceptable={summary['acceptable_source_hit_rate']:.2f}, "
            f"source_group={summary['source_group_hit_rate']:.2f}, "
            f"keyword={summary['keyword_hit_rate']:.2f}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RAGHub default /chat eval.")
    parser.add_argument("--queries", type=Path, default=QUERIES_PATH)
    parser.add_argument("--output", type=Path, default=RESULTS_PATH)
    parser.add_argument("--top-k", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = resolve_project_path(args.output)
    report = run_eval(
        queries_path=args.queries,
        output_path=output_path,
        top_k=args.top_k,
    )
    summary = report["summary"]
    all_cases = summary["all_cases"]

    print("RAGHub eval summary")
    print_summary_line("all", all_cases)

    for case_type, case_summary in summary["case_types"].items():
        print(f"{case_type}:")
        print_summary_line(case_type, case_summary)

    out_of_corpus = summary["case_types"].get("out_of_corpus")
    if out_of_corpus:
        print(
            "out_of_corpus_rejected: "
            f"{out_of_corpus['expected_unanswerable_rejected']}/"
            f"{out_of_corpus['expected_unanswerable_total']}"
        )

    print_breakdown("category_breakdown", all_cases["category_breakdown"])
    print_breakdown("difficulty_breakdown", all_cases["difficulty_breakdown"])

    print("case_type_notes:")
    for case_type, notes in summary["case_type_notes"].items():
        print(f"- {case_type}:")
        for note in notes:
            print(f"  - {note}")

    print(f"output: {output_path}")


if __name__ == "__main__":
    main()
