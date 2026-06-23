import scripts.run_llm_ab_review_v0_3 as ab_review


def test_build_review_scores_exact_grounded_answer():
    score, dimensions, comment = ab_review.build_review(
        expected_answerable=True,
        is_answerable=True,
        exact_source_hit=True,
        acceptable_source_hit=True,
        source_group_hit=True,
        keyword_rate=0.8,
    )

    assert score == 10
    assert dimensions == {
        "answerability": 2,
        "evidence_consistency": 2,
        "citation_support": 2,
        "completeness": 2,
        "hallucination_control": 2,
    }
    assert "exact expected source" in comment


def test_build_review_scores_expected_rejection():
    score, dimensions, comment = ab_review.build_review(
        expected_answerable=False,
        is_answerable=False,
        exact_source_hit=False,
        acceptable_source_hit=False,
        source_group_hit=False,
        keyword_rate=0.0,
    )

    assert score == 10
    assert all(value == 2 for value in dimensions.values())
    assert "Rejected expected out-of-corpus query" in comment


def test_compare_vector_and_hybrid_records_winner():
    results_by_mode = {
        "vector": [
            {
                "id": "q001",
                "query": "query",
                "review_score": 7,
                "review_comment": "vector comment",
            }
        ],
        "hybrid": [
            {
                "id": "q001",
                "query": "query",
                "review_score": 9,
                "review_comment": "hybrid comment",
            }
        ],
    }

    comparisons = ab_review.compare_vector_and_hybrid(results_by_mode)

    assert comparisons == [
        {
            "id": "q001",
            "query": "query",
            "vector_score": 7,
            "hybrid_score": 9,
            "winner": "hybrid",
            "reason": (
                "vector=7, hybrid=9; vector_comment=vector comment "
                "hybrid_comment=hybrid comment"
            ),
        }
    ]


def test_summarize_mode_tracks_metrics_and_out_of_corpus():
    results = [
        {
            "expected_source": "README.md",
            "expected_sources": ["README.md"],
            "expected_source_group": "group",
            "expected_answerable": True,
            "exact_source_hit": True,
            "acceptable_source_hit": True,
            "source_group_hit": True,
            "keyword_hit_count": 3,
            "expected_keyword_count": 4,
            "review_score": 9,
            "is_answerable": True,
        },
        {
            "expected_source": None,
            "expected_sources": [],
            "expected_source_group": None,
            "expected_answerable": False,
            "exact_source_hit": False,
            "acceptable_source_hit": False,
            "source_group_hit": False,
            "keyword_hit_count": 1,
            "expected_keyword_count": 2,
            "review_score": 10,
            "is_answerable": False,
        },
    ]

    summary = ab_review.summarize_mode(results)

    assert summary["total_queries"] == 2
    assert summary["average_score"] == 9.5
    assert summary["exact_source_hit_rate"] == 1
    assert summary["acceptable_source_hit_rate"] == 1
    assert summary["source_group_hit_rate"] == 1
    assert summary["keyword_hit_rate"] == 4 / 6
    assert summary["out_of_corpus_rejected"] == 1
    assert summary["out_of_corpus_total"] == 1

def test_build_summary_includes_category_and_difficulty_breakdowns():
    results_by_mode = {
        "vector": [
            {
                "id": "q001",
                "query": "query",
                "category": "api",
                "difficulty": "basic",
                "expected_source": "README.md",
                "expected_sources": ["README.md"],
                "expected_source_group": "group",
                "expected_answerable": True,
                "exact_source_hit": True,
                "acceptable_source_hit": True,
                "source_group_hit": True,
                "keyword_hit_count": 1,
                "expected_keyword_count": 1,
                "review_score": 10,
                "is_answerable": True,
                "review_comment": "ok",
            }
        ],
        "hybrid": [
            {
                "id": "q001",
                "query": "query",
                "category": "api",
                "difficulty": "basic",
                "expected_source": "README.md",
                "expected_sources": ["README.md"],
                "expected_source_group": "group",
                "expected_answerable": True,
                "exact_source_hit": True,
                "acceptable_source_hit": True,
                "source_group_hit": True,
                "keyword_hit_count": 1,
                "expected_keyword_count": 1,
                "review_score": 10,
                "is_answerable": True,
                "review_comment": "ok",
            }
        ],
    }

    comparisons = ab_review.compare_vector_and_hybrid(results_by_mode)
    summary = ab_review.build_summary(results_by_mode, comparisons)

    assert summary["category_breakdown"]["api"]["vector"]["total_queries"] == 1
    assert summary["difficulty_breakdown"]["basic"]["hybrid"]["average_score"] == 10


def test_main_accepts_eval_100_output_aliases(monkeypatch, tmp_path):
    output_json = tmp_path / "llm_ab_review_100_results.json"
    output_md = tmp_path / "llm_ab_review_100.md"

    fake_report = {
        "summary": {
            "by_mode": {
                "vector": {
                    "average_score": 10,
                    "exact_source_hit_rate": 1,
                    "acceptable_source_hit_rate": 1,
                    "source_group_hit_rate": 1,
                    "keyword_hit_rate": 1,
                    "out_of_corpus_rejected": 0,
                    "out_of_corpus_total": 0,
                },
                "hybrid": {
                    "average_score": 10,
                    "exact_source_hit_rate": 1,
                    "acceptable_source_hit_rate": 1,
                    "source_group_hit_rate": 1,
                    "keyword_hit_rate": 1,
                    "out_of_corpus_rejected": 0,
                    "out_of_corpus_total": 0,
                },
            },
            "vector_win_count": 0,
            "hybrid_win_count": 0,
            "tie_count": 1,
        },
        "results_by_mode": {},
        "comparisons": [],
    }

    monkeypatch.setattr(ab_review, "run_ab_review", lambda modes, queries_path, top_k=3, **kwargs: fake_report)
    monkeypatch.setattr(
        ab_review,
        "write_markdown_report",
        lambda report, path: path.write_text("md", encoding="utf-8"),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_llm_ab_review_v0_3.py",
            "--queries",
            str(tmp_path / "queries.jsonl"),
            "--modes",
            "vector",
            "hybrid",
            "--output",
            str(output_json),
            "--summary-output",
            str(output_md),
        ],
    )

    ab_review.main()

    assert output_json.exists()
    assert output_md.read_text(encoding="utf-8") == "md"
