from collections import Counter

from app.retrievers.bm25_retriever import BM25Retriever, tokenize


def build_test_retriever(chunks: list[dict]) -> BM25Retriever:
    retriever = BM25Retriever.__new__(BM25Retriever)
    retriever.chunks = chunks
    retriever.k1 = 1.5
    retriever.b = 0.75
    retriever.doc_tokens = [
        BM25Retriever._tokens_for_chunk(retriever, chunk)
        for chunk in chunks
    ]
    retriever.doc_term_counts = [
        Counter(tokens)
        for tokens in retriever.doc_tokens
    ]
    retriever.doc_lengths = [len(tokens) for tokens in retriever.doc_tokens]
    retriever.avg_doc_length = sum(retriever.doc_lengths) / len(retriever.doc_lengths)
    retriever.idf = BM25Retriever._build_idf(retriever)
    return retriever


def test_tokenize_keeps_api_and_field_tokens():
    tokens = tokenize(
        "POST /retrieve returns chunk_id and source_hit_rate. "
        "API key lives in DEEPSEEK_API_KEY and .env. "
        "Qdrant Milvus pgvector"
    )

    for expected in (
        "/retrieve",
        "chunk_id",
        "source_hit_rate",
        "api_key",
        "deepseek_api_key",
        ".env",
        "qdrant",
        "milvus",
        "pgvector",
    ):
        assert expected in tokens


def test_bm25_prefers_exact_api_field_chunk():
    retriever = build_test_retriever(
        [
            {
                "content": (
                    "POST /retrieve returns chunk_id, score, content, "
                    "source, file_type, and page."
                ),
                "source": "README.md",
                "file_type": "md",
                "page": None,
            },
            {
                "content": "POST /chat returns answer, sources, and reason.",
                "source": "docs/knowledge_base/raghub/chat_api_design.md",
                "file_type": "md",
                "page": None,
            },
        ],
    )

    results = retriever.search(
        query="RAGHub 的 /retrieve 接口返回 chunk_id score source",
        top_k=1,
    )

    assert results[0]["source"] == "README.md"
    assert results[0]["retrieval_score_detail"]["bm25_score"] > 0


def test_bm25_uses_visible_source_path_tokens():
    retriever = build_test_retriever(
        [
            {
                "content": "Default provider explanation.",
                "source": "docs/knowledge_base/raghub/mock_vs_deepseek.md",
                "file_type": "md",
                "page": None,
            },
            {
                "content": "Deployment boundary notes.",
                "source": "data/demo_corpus/ai_project_handbook/deployment_boundary.md",
                "file_type": "md",
                "page": None,
            },
        ],
    )

    results = retriever.search(query="mock DeepSeek provider", top_k=1)

    assert results[0]["source"] == "docs/knowledge_base/raghub/mock_vs_deepseek.md"
