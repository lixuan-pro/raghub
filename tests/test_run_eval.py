import scripts.run_eval as run_eval


def make_eval_result(
    is_answerable: bool,
    expected_answerable: bool,
    source_hit: bool = False,
    source_evaluable: bool = False,
    acceptable_source_hit: bool = False,
    acceptable_source_evaluable: bool = False,
    source_group_hit: bool = False,
    source_group_evaluable: bool = False,
    mrr_at_k: float = 0,
    recall_at_k: int = 0,
    keyword_hit_count: int = 0,
    expected_keywords: list[str] | None = None,
) -> dict:
    return {
        "is_answerable": is_answerable,
        "expected_answerable": expected_answerable,
        "answerable_correct": is_answerable == expected_answerable,
        "source_hit": source_hit,
        "source_evaluable": source_evaluable,
        "acceptable_source_hit": acceptable_source_hit,
        "acceptable_source_evaluable": acceptable_source_evaluable,
        "source_group_hit": source_group_hit,
        "source_group_evaluable": source_group_evaluable,
        "mrr_at_k": mrr_at_k,
        "recall_at_k": recall_at_k,
        "keyword_hit_count": keyword_hit_count,
        "expected_keywords": expected_keywords or [],
    }


def test_build_summary_tracks_answerability_metrics():
    results = [
        make_eval_result(
            is_answerable=True,
            expected_answerable=True,
            source_hit=True,
            source_evaluable=True,
            acceptable_source_hit=True,
            acceptable_source_evaluable=True,
            source_group_hit=True,
            source_group_evaluable=True,
            mrr_at_k=1,
            recall_at_k=1,
            keyword_hit_count=1,
            expected_keywords=["RAGHub"],
        ),
        make_eval_result(
            is_answerable=False,
            expected_answerable=False,
            keyword_hit_count=0,
            expected_keywords=["\u8d44\u6599\u4e0d\u8db3"],
        ),
    ]

    summary = run_eval.build_summary(results)

    assert summary["answerable_total"] == 2
    assert summary["answerable_correct"] == 2
    assert summary["answerable_accuracy"] == 1
    assert summary["expected_answerable_total"] == 1
    assert summary["expected_answerable_accepted"] == 1
    assert summary["expected_answerable_accept_rate"] == 1
    assert summary["expected_unanswerable_total"] == 1
    assert summary["expected_unanswerable_rejected"] == 1
    assert summary["expected_unanswerable_reject_rate"] == 1
    assert summary["exact_source_hit_rate"] == 1
    assert summary["acceptable_source_hit_rate"] == 1
    assert summary["source_group_hit_rate"] == 1
    assert summary["mrr_at_k"] == 1
    assert summary["recall_at_k"] == 1


def test_expected_sources_falls_back_to_legacy_expected_source():
    assert run_eval.get_expected_sources({"expected_source": "README.md"}) == [
        "README.md"
    ]
    assert run_eval.get_expected_sources({"expected_source": None}) == []


def test_source_grounding_helpers_track_acceptable_and_group_hits():
    queries = [
        {
            "expected_sources": [
                "README.md",
                "docs/knowledge_base/raghub/retrieve_api_design.md",
            ],
            "expected_source_group": "raghub_api_docs",
        }
    ]
    chunks = [
        {"source": "docs/knowledge_base/raghub/retrieve_api_design.md"},
    ]
    lookup = run_eval.build_source_group_lookup(queries)

    assert run_eval.is_acceptable_source_hit(
        queries[0]["expected_sources"],
        chunks,
    )
    assert run_eval.is_source_group_hit("raghub_api_docs", chunks, lookup)
    assert run_eval.first_source_hit_rank(queries[0]["expected_sources"], chunks) == 1
    assert run_eval.reciprocal_rank(2) == 0.5


def test_evaluate_query_records_expected_answerable(monkeypatch):
    def fake_generate_chat_response(query: str, top_k: int = 3):
        return {
            "answer": "\u5f53\u524d\u77e5\u8bc6\u5e93\u4e2d\u6ca1\u6709\u627e\u5230\u8db3\u591f\u4f9d\u636e\u3002",
            "is_answerable": False,
            "reason": "query_out_of_project_scope",
            "retrieved_chunks": [],
        }

    monkeypatch.setattr(run_eval, "generate_chat_response", fake_generate_chat_response)

    result = run_eval.evaluate_query(
        {
            "id": "q-test",
            "query": "RAGHub \u4f5c\u8005\u7684\u624b\u673a\u53f7\u662f\u591a\u5c11\uff1f",
            "case_type": "out_of_corpus",
            "expected_keywords": ["\u8d44\u6599\u4e0d\u8db3"],
            "expected_source": None,
            "expected_answerable": False,
        }
    )

    assert result["expected_answerable"] is False
    assert result["is_answerable"] is False
    assert result["answerable_correct"] is True
    assert result["reason"] == "query_out_of_project_scope"


def test_evaluate_query_records_source_grounding_metrics(monkeypatch):
    def fake_generate_chat_response(query: str, top_k: int = 3):
        return {
            "answer": "RAGHub retrieve fields include chunk_id and source.",
            "is_answerable": True,
            "reason": "retrieval_evidence_found",
            "retrieved_chunks": [
                {"source": "eval/llm_answer_review.md", "content": "noise", "score": 0.9},
                {
                    "source": "docs/knowledge_base/raghub/retrieve_api_design.md",
                    "content": "POST /retrieve returns chunk_id, score, content, source.",
                    "score": 0.8,
                },
            ],
        }

    monkeypatch.setattr(run_eval, "generate_chat_response", fake_generate_chat_response)

    item = {
        "id": "q-test",
        "query": "RAGHub 的 /retrieve 接口返回哪些字段？",
        "case_type": "in_corpus",
        "expected_keywords": ["chunk_id", "source"],
        "expected_source": "README.md",
        "expected_sources": [
            "README.md",
            "docs/knowledge_base/raghub/retrieve_api_design.md",
        ],
        "expected_source_group": "raghub_api_docs",
        "expected_answerable": True,
    }
    lookup = run_eval.build_source_group_lookup([item])

    result = run_eval.evaluate_query(
        item,
        source_group_lookup=lookup,
    )

    assert result["source_hit"] is False
    assert result["exact_source_hit"] is False
    assert result["acceptable_source_hit"] is True
    assert result["source_group_hit"] is True
    assert result["source_hit_rank"] == 2
    assert result["mrr_at_k"] == 0.5
    assert result["recall_at_k"] == 1
