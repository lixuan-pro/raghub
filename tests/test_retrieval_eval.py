import scripts.run_retrieval_eval as retrieval_eval


def make_retrieval_result(
    *,
    category: str,
    difficulty: str,
    case_type: str = "in_corpus",
    expected_answerable: bool = True,
    exact_source_hit: bool = True,
    acceptable_source_hit: bool = True,
    source_group_hit: bool = True,
) -> dict:
    return {
        "id": "q-test",
        "query": "query",
        "category": category,
        "difficulty": difficulty,
        "case_type": case_type,
        "expected_answerable": expected_answerable,
        "expected_source": "README.md" if expected_answerable else None,
        "expected_sources": ["README.md"] if expected_answerable else [],
        "expected_source_group": "group" if expected_answerable else None,
        "top_sources": ["README.md"] if expected_answerable else [],
        "matched_keywords": ["RAGHub"] if expected_answerable else [],
        "expected_keywords": ["RAGHub"] if expected_answerable else [],
        "keyword_hit_count": 1 if expected_answerable else 0,
        "source_evaluable": expected_answerable,
        "acceptable_source_evaluable": expected_answerable,
        "source_group_evaluable": expected_answerable,
        "exact_source_hit": exact_source_hit,
        "acceptable_source_hit": acceptable_source_hit,
        "source_group_hit": source_group_hit,
        "source_hit_rank": 1 if acceptable_source_hit else None,
        "mrr_at_k": 1 if acceptable_source_hit else 0,
        "recall_at_k": 1 if acceptable_source_hit else 0,
    }


def test_build_summary_includes_category_and_difficulty_breakdowns():
    results = [
        make_retrieval_result(category="api", difficulty="basic"),
        make_retrieval_result(
            category="out_of_corpus",
            difficulty="hard",
            case_type="out_of_corpus",
            expected_answerable=False,
        ),
    ]

    summary = retrieval_eval.build_summary(results)

    assert summary["total_queries"] == 2
    assert summary["in_corpus_count"] == 1
    assert summary["out_of_corpus_count"] == 1
    assert summary["category_breakdown"]["api"]["total_queries"] == 1
    assert summary["difficulty_breakdown"]["basic"]["total_queries"] == 1
    assert summary["difficulty_breakdown"]["hard"]["out_of_corpus_count"] == 1


def test_run_retrieval_eval_writes_requested_output(monkeypatch, tmp_path):
    queries = [
        {
            "id": "q001",
            "query": "query",
            "category": "api",
            "difficulty": "basic",
            "case_type": "in_corpus",
            "expected_answerable": True,
            "expected_source": "README.md",
            "expected_sources": ["README.md"],
            "expected_source_group": "group",
            "expected_keywords": ["RAGHub"],
        }
    ]

    class FakeRetriever:
        def search(self, query: str, top_k: int = 3):
            return [
                {
                    "source": "README.md",
                    "content": "RAGHub",
                    "score": 1.0,
                }
            ]

    monkeypatch.setattr(retrieval_eval, "load_eval_queries", lambda path: queries)
    monkeypatch.setattr(
        retrieval_eval,
        "build_retrievers",
        lambda queries, top_k=3: {"vector": FakeRetriever()},
    )
    old_output = tmp_path / "retrieval_comparison.json"
    old_output.write_text("old", encoding="utf-8")
    output = tmp_path / "retrieval_comparison_100.json"

    report = retrieval_eval.run_retrieval_eval(
        queries_path=tmp_path / "queries.jsonl",
        output_path=output,
    )

    assert output.exists()
    assert old_output.read_text(encoding="utf-8") == "old"
    assert report["summary"]["vector"]["category_breakdown"]["api"]["total_queries"] == 1
