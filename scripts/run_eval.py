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


def evaluate_query(item: dict[str, Any], top_k: int = 3) -> dict[str, Any]:
    response = generate_chat_response(query=item["query"], top_k=top_k)
    retrieved_chunks = response["retrieved_chunks"]
    expected_keywords = item.get("expected_keywords", [])
    expected_source = item.get("expected_source")
    expected_answerable = item.get("expected_answerable")
    is_answerable = bool(response.get("is_answerable"))

    top_score = retrieved_chunks[0]["score"] if retrieved_chunks else None
    matched_keywords = match_keywords(
        expected_keywords=expected_keywords,
        answer=response["answer"],
        retrieved_chunks=retrieved_chunks,
    )

    return {
        "id": item["id"],
        "query": item["query"],
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
        "source_hit": is_source_hit(expected_source, retrieved_chunks),
        "source_evaluable": bool(expected_source),
    }


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    source_evaluable = [item for item in results if item.get("source_evaluable")]
    source_hits = sum(1 for item in source_evaluable if item["source_hit"])
    total_keyword_hits = sum(item["keyword_hit_count"] for item in results)
    total_expected_keywords = sum(len(item["expected_keywords"]) for item in results)
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

    return {
        "total": len(results),
        "answerable_count": answerable_count,
        "answerable_total": len(answerable_evaluable),
        "answerable_correct": answerable_correct,
        "answerable_accuracy": (
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
        "source_hits": source_hits,
        "source_evaluable": len(source_evaluable),
        "source_hit_rate": (
            source_hits / len(source_evaluable)
            if source_evaluable
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


def run_eval() -> dict[str, Any]:
    queries = load_eval_queries()
    results = [evaluate_query(item) for item in queries]
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

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return report


def print_summary_line(prefix: str, summary: dict[str, Any]) -> None:
    print(f"{prefix}_total: {summary['total']}")
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
        f"{prefix}_keyword_hits: "
        f"{summary['keyword_hits']}/{summary['expected_keywords']}"
    )
    print(f"{prefix}_keyword_hit_rate: {summary['keyword_hit_rate']:.2f}")


def main() -> None:
    report = run_eval()
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

    print("case_type_notes:")
    for case_type, notes in summary["case_type_notes"].items():
        print(f"- {case_type}:")
        for note in notes:
            print(f"  - {note}")

    print(f"output: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
