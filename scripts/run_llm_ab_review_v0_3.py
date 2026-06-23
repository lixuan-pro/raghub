import argparse
import json
import os
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.llm.base import LLMProviderError
from app.services.rag_service import generate_chat_response
from scripts.run_eval import (
    build_source_group_lookup,
    get_expected_sources,
    is_acceptable_source_hit,
    is_source_group_hit,
    is_source_hit,
    load_eval_queries,
    match_keywords,
    resolve_project_path,
)


DEFAULT_MODES = ("vector", "hybrid")
SUPPORTED_MODES = ("vector", "bm25", "hybrid", "hybrid_rerank")
DEFAULT_TOP_K = 3
QUERIES_PATH = PROJECT_ROOT / "eval" / "queries.jsonl"
RESULTS_PATH = PROJECT_ROOT / "eval" / "llm_ab_review_v0_3_results.json"
REPORT_PATH = PROJECT_ROOT / "eval" / "llm_ab_review_v0_3.md"


def chunk_preview(chunk: dict[str, Any], limit: int = 160) -> dict[str, Any]:
    content = str(chunk.get("content") or "").strip()
    return {
        "chunk_id": str(chunk.get("chunk_id")),
        "score": float(chunk.get("score") or 0),
        "source": chunk.get("source") or "",
        "content_preview": content[:limit],
    }


def keyword_hit_rate(matched_keywords: list[str], expected_keywords: list[str]) -> float:
    if not expected_keywords:
        return 0.0
    return len(matched_keywords) / len(expected_keywords)


def score_answerability(expected_answerable: bool | None, is_answerable: bool) -> int:
    if expected_answerable is None:
        return 1
    return 2 if expected_answerable == is_answerable else 0


def score_evidence_consistency(
    expected_answerable: bool | None,
    is_answerable: bool,
    acceptable_source_hit: bool,
    source_group_hit: bool,
) -> int:
    if expected_answerable is False:
        return 2 if not is_answerable else 0
    if not is_answerable:
        return 0
    if acceptable_source_hit:
        return 2
    if source_group_hit:
        return 1
    return 0


def score_citation_support(
    expected_answerable: bool | None,
    is_answerable: bool,
    exact_source_hit: bool,
    acceptable_source_hit: bool,
    source_group_hit: bool,
) -> int:
    if expected_answerable is False:
        return 2 if not is_answerable else 0
    if not is_answerable:
        return 0
    if exact_source_hit:
        return 2
    if acceptable_source_hit or source_group_hit:
        return 1
    return 0


def score_completeness(
    expected_answerable: bool | None,
    is_answerable: bool,
    rate: float,
) -> int:
    if expected_answerable is False:
        return 2 if not is_answerable else 0
    if not is_answerable:
        return 0
    if rate >= 0.75:
        return 2
    if rate > 0:
        return 1
    return 0


def score_hallucination_control(
    expected_answerable: bool | None,
    is_answerable: bool,
    acceptable_source_hit: bool,
    source_group_hit: bool,
) -> int:
    if expected_answerable is False:
        return 2 if not is_answerable else 0
    if not is_answerable:
        return 1
    if acceptable_source_hit or source_group_hit:
        return 2
    return 1


def build_review(
    *,
    expected_answerable: bool | None,
    is_answerable: bool,
    exact_source_hit: bool,
    acceptable_source_hit: bool,
    source_group_hit: bool,
    keyword_rate: float,
) -> tuple[int, dict[str, int], str]:
    dimensions = {
        "answerability": score_answerability(
            expected_answerable=expected_answerable,
            is_answerable=is_answerable,
        ),
        "evidence_consistency": score_evidence_consistency(
            expected_answerable=expected_answerable,
            is_answerable=is_answerable,
            acceptable_source_hit=acceptable_source_hit,
            source_group_hit=source_group_hit,
        ),
        "citation_support": score_citation_support(
            expected_answerable=expected_answerable,
            is_answerable=is_answerable,
            exact_source_hit=exact_source_hit,
            acceptable_source_hit=acceptable_source_hit,
            source_group_hit=source_group_hit,
        ),
        "completeness": score_completeness(
            expected_answerable=expected_answerable,
            is_answerable=is_answerable,
            rate=keyword_rate,
        ),
        "hallucination_control": score_hallucination_control(
            expected_answerable=expected_answerable,
            is_answerable=is_answerable,
            acceptable_source_hit=acceptable_source_hit,
            source_group_hit=source_group_hit,
        ),
    }
    score = sum(dimensions.values())

    if expected_answerable is False:
        comment = (
            "Rejected expected out-of-corpus query."
            if not is_answerable
            else "Answered expected out-of-corpus query."
        )
    elif exact_source_hit:
        comment = "Answerable with exact expected source in retrieved chunks."
    elif acceptable_source_hit:
        comment = "Answerable with an acceptable source, but not exact expected source."
    elif source_group_hit:
        comment = "Answerable with related source group evidence."
    elif is_answerable:
        comment = "Answerable, but retrieved sources do not match expected grounding."
    else:
        comment = "Expected answerable query was rejected."

    comment = f"{comment} Keyword coverage={keyword_rate:.2f}."
    return score, dimensions, comment


def evaluate_query_for_mode(
    *,
    item: dict[str, Any],
    mode: str,
    top_k: int,
    source_group_lookup: dict[str, set[str]],
) -> dict[str, Any]:
    os.environ["RETRIEVER_PROVIDER"] = mode
    response = generate_chat_response(query=item["query"], top_k=top_k)
    retrieved_chunks = response["retrieved_chunks"]
    expected_keywords = item.get("expected_keywords", [])
    expected_source = item.get("expected_source")
    expected_sources = get_expected_sources(item)
    expected_source_group = item.get("expected_source_group")
    expected_answerable = item.get("expected_answerable")
    matched_keywords = match_keywords(
        expected_keywords=expected_keywords,
        answer=response["answer"],
        retrieved_chunks=retrieved_chunks,
    )
    rate = keyword_hit_rate(
        matched_keywords=matched_keywords,
        expected_keywords=expected_keywords,
    )
    exact_hit = is_source_hit(
        expected_source=expected_source,
        retrieved_chunks=retrieved_chunks,
    )
    acceptable_hit = is_acceptable_source_hit(
        expected_sources=expected_sources,
        retrieved_chunks=retrieved_chunks,
    )
    group_hit = is_source_group_hit(
        expected_source_group=expected_source_group,
        retrieved_chunks=retrieved_chunks,
        source_group_lookup=source_group_lookup,
    )
    is_answerable = bool(response.get("is_answerable"))
    review_score, dimensions, comment = build_review(
        expected_answerable=expected_answerable,
        is_answerable=is_answerable,
        exact_source_hit=exact_hit,
        acceptable_source_hit=acceptable_hit,
        source_group_hit=group_hit,
        keyword_rate=rate,
    )

    return {
        "id": item["id"],
        "query": item["query"],
        "category": item.get("category", "uncategorized"),
        "difficulty": item.get("difficulty", "unknown"),
        "mode": mode,
        "case_type": item.get("case_type", "in_corpus"),
        "expected_answerable": expected_answerable,
        "expected_source": expected_source,
        "expected_sources": expected_sources,
        "expected_source_group": expected_source_group,
        "answer": response["answer"],
        "sources": [
            source.get("source") or ""
            for source in response.get("sources", [])
        ],
        "retrieved_chunks": [chunk_preview(chunk) for chunk in retrieved_chunks],
        "is_answerable": is_answerable,
        "reason": response.get("reason"),
        "exact_source_hit": exact_hit,
        "acceptable_source_hit": acceptable_hit,
        "source_group_hit": group_hit,
        "matched_keywords": matched_keywords,
        "expected_keywords": expected_keywords,
        "keyword_hit_count": len(matched_keywords),
        "expected_keyword_count": len(expected_keywords),
        "keyword_hit_rate": rate,
        "review_score": review_score,
        "review_dimensions": dimensions,
        "review_comment": comment,
    }


def summarize_mode(results: list[dict[str, Any]]) -> dict[str, Any]:
    source_evaluable = [
        item for item in results if item.get("expected_source")
    ]
    acceptable_evaluable = [
        item for item in results if item.get("expected_sources")
    ]
    source_group_evaluable = [
        item for item in results if item.get("expected_source_group")
    ]
    out_of_corpus = [
        item for item in results if item.get("expected_answerable") is False
    ]
    total_keyword_hits = sum(int(item["keyword_hit_count"]) for item in results)
    total_expected_keywords = sum(
        int(item["expected_keyword_count"]) for item in results
    )

    return {
        "total_queries": len(results),
        "in_corpus_count": sum(1 for item in results if item.get("case_type", "in_corpus") == "in_corpus"),
        "out_of_corpus_count": len(out_of_corpus),
        "average_score": (
            sum(float(item["review_score"]) for item in results) / len(results)
            if results
            else 0.0
        ),
        "exact_source_hit_rate": (
            sum(1 for item in source_evaluable if item["exact_source_hit"])
            / len(source_evaluable)
            if source_evaluable
            else 0.0
        ),
        "acceptable_source_hit_rate": (
            sum(1 for item in acceptable_evaluable if item["acceptable_source_hit"])
            / len(acceptable_evaluable)
            if acceptable_evaluable
            else 0.0
        ),
        "source_group_hit_rate": (
            sum(1 for item in source_group_evaluable if item["source_group_hit"])
            / len(source_group_evaluable)
            if source_group_evaluable
            else 0.0
        ),
        "keyword_hit_rate": (
            total_keyword_hits / total_expected_keywords
            if total_expected_keywords
            else 0.0
        ),
        "out_of_corpus_rejected": sum(
            1 for item in out_of_corpus if not item["is_answerable"]
        ),
        "out_of_corpus_total": len(out_of_corpus),
    }


def compare_vector_and_hybrid(
    results_by_mode: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    if "vector" not in results_by_mode or "hybrid" not in results_by_mode:
        return []

    vector_by_id = {item["id"]: item for item in results_by_mode["vector"]}
    hybrid_by_id = {item["id"]: item for item in results_by_mode["hybrid"]}
    comparisons = []

    for query_id in sorted(vector_by_id):
        if query_id not in hybrid_by_id:
            continue

        vector_item = vector_by_id[query_id]
        hybrid_item = hybrid_by_id[query_id]
        vector_score = int(vector_item["review_score"])
        hybrid_score = int(hybrid_item["review_score"])

        if vector_score > hybrid_score:
            winner = "vector"
        elif hybrid_score > vector_score:
            winner = "hybrid"
        else:
            winner = "tie"

        comparisons.append(
            {
                "id": query_id,
                "query": vector_item["query"],
                "vector_score": vector_score,
                "hybrid_score": hybrid_score,
                "winner": winner,
                "reason": (
                    f"vector={vector_score}, hybrid={hybrid_score}; "
                    f"vector_comment={vector_item['review_comment']} "
                    f"hybrid_comment={hybrid_item['review_comment']}"
                ),
            }
        )

    return comparisons


def build_mode_breakdown(
    results_by_mode: dict[str, list[dict[str, Any]]],
    field: str,
) -> dict[str, dict[str, dict[str, Any]]]:
    groups = sorted(
        {
            str(item.get(field) or "unknown")
            for results in results_by_mode.values()
            for item in results
        }
    )
    return {
        group: {
            mode: summarize_mode(
                [
                    item
                    for item in results
                    if str(item.get(field) or "unknown") == group
                ]
            )
            for mode, results in results_by_mode.items()
        }
        for group in groups
    }


def build_summary(
    results_by_mode: dict[str, list[dict[str, Any]]],
    comparisons: list[dict[str, Any]],
) -> dict[str, Any]:
    by_mode = {
        mode: summarize_mode(results)
        for mode, results in results_by_mode.items()
    }
    summary: dict[str, Any] = {
        "total_queries": (
            len(next(iter(results_by_mode.values())))
            if results_by_mode
            else 0
        ),
        "by_mode": by_mode,
        "vector_win_count": sum(
            1 for item in comparisons if item["winner"] == "vector"
        ),
        "hybrid_win_count": sum(
            1 for item in comparisons if item["winner"] == "hybrid"
        ),
        "tie_count": sum(1 for item in comparisons if item["winner"] == "tie"),
        "category_breakdown": build_mode_breakdown(results_by_mode, "category"),
        "difficulty_breakdown": build_mode_breakdown(results_by_mode, "difficulty"),
    }

    for mode, mode_summary in by_mode.items():
        for key, value in mode_summary.items():
            summary[f"{mode}_{key}"] = value

    return summary


def format_rate(value: float) -> str:
    return f"{value:.2f}"


def representative_cases(
    results_by_mode: dict[str, list[dict[str, Any]]],
    comparisons: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    vector_by_id = {
        item["id"]: item
        for item in results_by_mode.get("vector", [])
    }
    hybrid_by_id = {
        item["id"]: item
        for item in results_by_mode.get("hybrid", [])
    }

    buckets = {
        "hybrid_better": [],
        "vector_better": [],
        "tie": [],
        "out_of_corpus": [],
    }
    for item in comparisons:
        query_id = item["id"]
        vector_item = vector_by_id.get(query_id)
        hybrid_item = hybrid_by_id.get(query_id)
        if not vector_item or not hybrid_item:
            continue

        payload = {
            "id": query_id,
            "query": item["query"],
            "category": item.get("category", "uncategorized"),
            "difficulty": item.get("difficulty", "unknown"),
            "vector_score": item["vector_score"],
            "hybrid_score": item["hybrid_score"],
            "vector_comment": vector_item["review_comment"],
            "hybrid_comment": hybrid_item["review_comment"],
        }

        if vector_item.get("case_type") == "out_of_corpus":
            buckets["out_of_corpus"].append(payload)
        elif item["winner"] == "hybrid":
            buckets["hybrid_better"].append(payload)
        elif item["winner"] == "vector":
            buckets["vector_better"].append(payload)
        else:
            buckets["tie"].append(payload)

    return {
        key: values[:5]
        for key, values in buckets.items()
    }


def write_markdown_report(report: dict[str, Any], path: Path) -> None:
    summary = report["summary"]
    by_mode = summary["by_mode"]
    vector = by_mode.get("vector", {})
    hybrid = by_mode.get("hybrid", {})
    cases = representative_cases(
        results_by_mode=report["results_by_mode"],
        comparisons=report["comparisons"],
    )
    total_queries = summary.get("total_queries", 0)
    title = (
        "RAGHub Eval-100 DeepSeek A/B Review"
        if total_queries == 100
        else "RAGHub v0.3-lite DeepSeek A/B Review"
    )

    lines = [
        f"# {title}",
        "",
        f"本评测使用现有 `/chat` 链路和 DeepSeek provider，对 `eval/queries.jsonl` 的 {total_queries} 条 query 做 vector 与 hybrid 的端到端对比。评分为轻量规则化 review，不是 LLM-as-judge，也不是生产级准确率。",
        "",
        "## Summary",
        "",
        "| metric | vector | hybrid |",
        "| --- | ---: | ---: |",
        f"| average_score | {format_rate(vector.get('average_score', 0.0))} | {format_rate(hybrid.get('average_score', 0.0))} |",
        f"| exact_source_hit_rate | {format_rate(vector.get('exact_source_hit_rate', 0.0))} | {format_rate(hybrid.get('exact_source_hit_rate', 0.0))} |",
        f"| acceptable_source_hit_rate | {format_rate(vector.get('acceptable_source_hit_rate', 0.0))} | {format_rate(hybrid.get('acceptable_source_hit_rate', 0.0))} |",
        f"| source_group_hit_rate | {format_rate(vector.get('source_group_hit_rate', 0.0))} | {format_rate(hybrid.get('source_group_hit_rate', 0.0))} |",
        f"| keyword_hit_rate | {format_rate(vector.get('keyword_hit_rate', 0.0))} | {format_rate(hybrid.get('keyword_hit_rate', 0.0))} |",
        f"| out_of_corpus_rejected | {vector.get('out_of_corpus_rejected', 0)}/{vector.get('out_of_corpus_total', 0)} | {hybrid.get('out_of_corpus_rejected', 0)}/{hybrid.get('out_of_corpus_total', 0)} |",
        "",
        "## Winner Distribution",
        "",
        f"- vector wins: {summary['vector_win_count']}",
        f"- hybrid wins: {summary['hybrid_win_count']}",
        f"- ties: {summary['tie_count']}",
        "",
        "## Category Breakdown",
        "",
        "| category | vector_avg | hybrid_avg | vector_exact | hybrid_exact |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for category, modes in summary.get("category_breakdown", {}).items():
        vector_category = modes.get("vector", {})
        hybrid_category = modes.get("hybrid", {})
        lines.append(
            f"| {category} | {format_rate(vector_category.get('average_score', 0.0))} | "
            f"{format_rate(hybrid_category.get('average_score', 0.0))} | "
            f"{format_rate(vector_category.get('exact_source_hit_rate', 0.0))} | "
            f"{format_rate(hybrid_category.get('exact_source_hit_rate', 0.0))} |"
        )

    lines.extend(
        [
            "",
            "## Difficulty Breakdown",
            "",
            "| difficulty | vector_avg | hybrid_avg | vector_exact | hybrid_exact |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for difficulty, modes in summary.get("difficulty_breakdown", {}).items():
        vector_difficulty = modes.get("vector", {})
        hybrid_difficulty = modes.get("hybrid", {})
        lines.append(
            f"| {difficulty} | {format_rate(vector_difficulty.get('average_score', 0.0))} | "
            f"{format_rate(hybrid_difficulty.get('average_score', 0.0))} | "
            f"{format_rate(vector_difficulty.get('exact_source_hit_rate', 0.0))} | "
            f"{format_rate(hybrid_difficulty.get('exact_source_hit_rate', 0.0))} |"
        )

    lines.extend(
        [
            "",
            "## Representative Cases",
            "",
        ]
    )

    labels = {
        "hybrid_better": "Hybrid better",
        "vector_better": "Vector better",
        "tie": "Tie",
        "out_of_corpus": "Out-of-corpus",
    }
    for key, label in labels.items():
        lines.append(f"### {label}")
        lines.append("")
        if not cases[key]:
            lines.append("- None in this run.")
        for item in cases[key]:
            lines.append(
                f"- `{item['id']}` {item['query']} "
                f"(category={item['category']}, difficulty={item['difficulty']}, "
                f"vector={item['vector_score']}, hybrid={item['hybrid_score']})"
            )
        lines.append("")

    if hybrid.get("average_score", 0.0) > vector.get("average_score", 0.0):
        conclusion = "在本轮小型分层评测中，hybrid 相比 vector 有一定提升。"
    elif hybrid.get("average_score", 0.0) == vector.get("average_score", 0.0):
        conclusion = "hybrid 提升 retrieval coverage，但 end-to-end 回答质量提升有限。"
    else:
        conclusion = "hybrid 引入更多相关上下文，但也可能带来噪声，因此不适合作为默认检索模式。"

    lines.extend(
        [
            "## Conclusion",
            "",
            conclusion,
            "",
            "Eval-100 仍是项目级小型评测，不是生产级 benchmark。",
            "",
            "当前不建议把 hybrid 设为默认检索模式；默认 `/retrieve` 和 `/chat` 仍保持 vector。",
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def load_checkpoint(
    checkpoint_path: Path | None,
    modes: list[str],
) -> dict[str, list[dict[str, Any]]]:
    if not checkpoint_path or not checkpoint_path.exists():
        return {}

    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    checkpoint_results = checkpoint.get("results_by_mode", {})
    return {
        mode: list(checkpoint_results.get(mode, []))
        for mode in modes
    }


def write_checkpoint(
    checkpoint_path: Path | None,
    *,
    modes: list[str],
    top_k: int,
    results_by_mode: dict[str, list[dict[str, Any]]],
) -> None:
    if not checkpoint_path:
        return

    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(
        json.dumps(
            {
                "review_date": date.today().isoformat(),
                "provider": "deepseek",
                "modes": modes,
                "top_k": top_k,
                "checkpoint": True,
                "results_by_mode": results_by_mode,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def evaluate_query_for_mode_with_retries(
    *,
    item: dict[str, Any],
    mode: str,
    top_k: int,
    source_group_lookup: dict[str, set[str]],
    max_retries: int,
    retry_delay_seconds: float,
) -> dict[str, Any]:
    attempt = 0
    while True:
        try:
            return evaluate_query_for_mode(
                item=item,
                mode=mode,
                top_k=top_k,
                source_group_lookup=source_group_lookup,
            )
        except LLMProviderError as exc:
            if attempt >= max_retries:
                raise
            attempt += 1
            print(
                f"[{mode}] {item['id']} retry {attempt}/{max_retries}: {exc}",
                file=sys.stderr,
            )
            time.sleep(retry_delay_seconds)


def run_ab_review(
    modes: list[str],
    queries_path: Path = QUERIES_PATH,
    top_k: int = DEFAULT_TOP_K,
    checkpoint_path: Path | None = None,
    max_retries: int = 2,
    retry_delay_seconds: float = 5.0,
) -> dict[str, Any]:
    if not os.getenv("DEEPSEEK_API_KEY"):
        raise RuntimeError("DEEPSEEK_API_KEY is required but was not found")

    queries = load_eval_queries(queries_path)
    source_group_lookup = build_source_group_lookup(queries)
    results_by_mode: dict[str, list[dict[str, Any]]] = load_checkpoint(
        checkpoint_path=checkpoint_path,
        modes=modes,
    )
    original_llm_provider = os.environ.get("LLM_PROVIDER")
    original_retriever_provider = os.environ.get("RETRIEVER_PROVIDER")

    try:
        os.environ["LLM_PROVIDER"] = "deepseek"
        for mode in modes:
            mode_results = results_by_mode.setdefault(mode, [])
            completed_ids = {item["id"] for item in mode_results}
            for index, item in enumerate(queries, start=1):
                if item["id"] in completed_ids:
                    print(f"[{mode}] {index}/{len(queries)} {item['id']} skipped")
                    continue

                print(f"[{mode}] {index}/{len(queries)} {item['id']}")
                mode_results.append(
                    evaluate_query_for_mode_with_retries(
                        item=item,
                        mode=mode,
                        top_k=top_k,
                        source_group_lookup=source_group_lookup,
                        max_retries=max_retries,
                        retry_delay_seconds=retry_delay_seconds,
                    )
                )
                completed_ids.add(item["id"])
                write_checkpoint(
                    checkpoint_path,
                    modes=modes,
                    top_k=top_k,
                    results_by_mode=results_by_mode,
                )
    finally:
        if original_llm_provider is None:
            os.environ.pop("LLM_PROVIDER", None)
        else:
            os.environ["LLM_PROVIDER"] = original_llm_provider

        if original_retriever_provider is None:
            os.environ.pop("RETRIEVER_PROVIDER", None)
        else:
            os.environ["RETRIEVER_PROVIDER"] = original_retriever_provider

    comparisons = compare_vector_and_hybrid(results_by_mode)
    summary = build_summary(
        results_by_mode=results_by_mode,
        comparisons=comparisons,
    )

    return {
        "review_date": date.today().isoformat(),
        "provider": "deepseek",
        "modes": modes,
        "top_k": top_k,
        "review_method": "DeepSeek generation with lightweight rule-based scoring",
        "summary": summary,
        "comparisons": comparisons,
        "results_by_mode": results_by_mode,
        "results": [
            item
            for mode in modes
            for item in results_by_mode.get(mode, [])
        ],
    }

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run RAGHub DeepSeek vector/hybrid A/B review."
    )
    parser.add_argument("--queries", type=Path, default=QUERIES_PATH)
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=SUPPORTED_MODES,
        default=list(DEFAULT_MODES),
    )
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--retry-delay-seconds", type=float, default=5.0)
    parser.add_argument(
        "--checkpoint-output",
        type=Path,
        default=None,
    )
    parser.add_argument(
        "--output-json",
        "--output",
        dest="output_json",
        type=Path,
        default=RESULTS_PATH,
    )
    parser.add_argument(
        "--output-md",
        "--summary-output",
        dest="output_md",
        type=Path,
        default=REPORT_PATH,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_json = resolve_project_path(args.output_json)
    output_md = resolve_project_path(args.output_md)
    checkpoint_output = (
        resolve_project_path(args.checkpoint_output)
        if args.checkpoint_output
        else output_json.with_name(f"{output_json.stem}_checkpoint.json")
    )
    report = run_ab_review(
        modes=args.modes,
        queries_path=args.queries,
        top_k=args.top_k,
        checkpoint_path=checkpoint_output,
        max_retries=args.max_retries,
        retry_delay_seconds=args.retry_delay_seconds,
    )
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_markdown_report(report=report, path=output_md)
    if checkpoint_output.exists():
        checkpoint_output.unlink()

    summary = report["summary"]
    print("RAGHub DeepSeek A/B review")
    for mode in args.modes:
        mode_summary = summary["by_mode"][mode]
        print(
            f"{mode}: "
            f"average_score={mode_summary['average_score']:.2f}, "
            f"exact={mode_summary['exact_source_hit_rate']:.2f}, "
            f"acceptable={mode_summary['acceptable_source_hit_rate']:.2f}, "
            f"source_group={mode_summary['source_group_hit_rate']:.2f}, "
            f"keyword={mode_summary['keyword_hit_rate']:.2f}, "
            f"out_of_corpus_rejected="
            f"{mode_summary['out_of_corpus_rejected']}/"
            f"{mode_summary['out_of_corpus_total']}"
        )
    print(
        "winner_distribution: "
        f"vector={summary['vector_win_count']}, "
        f"hybrid={summary['hybrid_win_count']}, "
        f"tie={summary['tie_count']}"
    )
    print(f"output_json: {output_json}")
    print(f"output_md: {output_md}")


if __name__ == "__main__":
    main()
