from app.retrievers.hybrid_retriever import HybridRetriever, normalize_scores


class FakeRetriever:
    def __init__(self, results: list[dict]) -> None:
        self.results = results

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        return self.results[:top_k]


def make_result(
    chunk_id: str,
    score: float,
    content: str = "content",
    source: str = "README.md",
) -> dict:
    return {
        "chunk_id": chunk_id,
        "score": score,
        "content": content,
        "source": source,
        "file_type": "md",
        "page": None,
    }


def test_normalize_scores_handles_range_and_ties():
    assert normalize_scores({"a": 2.0, "b": 4.0}) == {"a": 0.0, "b": 1.0}
    assert normalize_scores({"a": 3.0, "b": 3.0}) == {"a": 1.0, "b": 1.0}
    assert normalize_scores({"a": 0.0, "b": 0.0}) == {"a": 0.0, "b": 0.0}


def test_hybrid_merges_candidates_by_chunk_id_and_keeps_missing_scores():
    retriever = HybridRetriever(
        vector_retriever=FakeRetriever(
            [
                make_result("1", 0.9, source="a.md"),
                make_result("2", 0.7, source="b.md"),
            ]
        ),
        bm25_retriever=FakeRetriever(
            [
                make_result("2", 5.0, source="b.md"),
                make_result("3", 10.0, source="c.md"),
            ]
        ),
        vector_top_n=10,
        bm25_top_n=10,
    )

    results = retriever.search(query="RAGHub source", top_k=3)
    by_chunk_id = {item["chunk_id"]: item for item in results}

    assert set(by_chunk_id) == {"1", "2", "3"}
    assert by_chunk_id["2"]["retrieval_score_detail"]["vector_score"] == 0.7
    assert by_chunk_id["2"]["retrieval_score_detail"]["bm25_score"] == 5.0
    assert by_chunk_id["1"]["retrieval_score_detail"]["bm25_score"] == 0.0
    assert by_chunk_id["3"]["retrieval_score_detail"]["vector_score"] == 0.0


def test_hybrid_rerank_can_promote_source_and_entity_match():
    retriever = HybridRetriever(
        vector_retriever=FakeRetriever(
            [
                make_result(
                    "1",
                    0.5,
                    content="general backend notes",
                    source="docs/general.md",
                ),
                make_result(
                    "2",
                    0.5,
                    content="API key should stay in .env with placeholders.",
                    source="data/demo_corpus/ai_project_handbook/security_and_api_key_policy.md",
                ),
            ]
        ),
        bm25_retriever=FakeRetriever([]),
        alpha=0.0,
        beta=0.0,
        gamma=0.0,
        use_rerank=True,
    )

    results = retriever.search(query="API key .env", top_k=2)

    assert results[0]["chunk_id"] == "2"
    assert results[0]["retrieval_score_detail"]["rerank_score"] > 0
