import scripts.run_eval as run_eval


def make_eval_result(
    is_answerable: bool,
    expected_answerable: bool,
    source_hit: bool = False,
    source_evaluable: bool = False,
    keyword_hit_count: int = 0,
    expected_keywords: list[str] | None = None,
) -> dict:
    return {
        "is_answerable": is_answerable,
        "expected_answerable": expected_answerable,
        "answerable_correct": is_answerable == expected_answerable,
        "source_hit": source_hit,
        "source_evaluable": source_evaluable,
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
