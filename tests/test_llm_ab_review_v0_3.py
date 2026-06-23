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
