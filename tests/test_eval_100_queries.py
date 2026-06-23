import json
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUERIES_PATH = PROJECT_ROOT / "eval" / "queries.jsonl"

EXPECTED_CATEGORY_COUNTS = {
    "api": 12,
    "loader_chunking": 10,
    "embedding_retrieval": 10,
    "llm_provider": 10,
    "citation_no_answer": 10,
    "eval_badcase": 12,
    "rag_engineering": 14,
    "demo_corpus": 10,
    "out_of_corpus": 12,
}
VALID_DIFFICULTIES = {"basic", "medium", "hard"}


def load_queries() -> list[dict]:
    return [
        json.loads(line)
        for line in QUERIES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_eval_100_has_exact_count_ids_and_distribution():
    queries = load_queries()

    assert len(queries) == 100
    assert [item["id"] for item in queries] == [
        f"q{index:03d}" for index in range(1, 101)
    ]
    assert len({item["id"] for item in queries}) == 100
    assert Counter(item["category"] for item in queries) == EXPECTED_CATEGORY_COUNTS


def test_eval_100_difficulty_values_and_category_coverage():
    queries = load_queries()
    difficulties_by_category = defaultdict(set)

    for item in queries:
        assert item["difficulty"] in VALID_DIFFICULTIES
        difficulties_by_category[item["category"]].add(item["difficulty"])

    for category in EXPECTED_CATEGORY_COUNTS:
        assert difficulties_by_category[category] == VALID_DIFFICULTIES


def test_eval_100_out_of_corpus_schema_is_unanswerable():
    queries = load_queries()

    for item in queries:
        if item["category"] != "out_of_corpus":
            continue
        assert item["case_type"] == "out_of_corpus"
        assert item["expected_answerable"] is False
        assert item["expected_source"] is None
        assert item["expected_sources"] == []
        assert item["expected_source_group"] is None
        assert item["expected_keywords"] == []


def test_eval_100_in_corpus_schema_has_grounding_labels():
    queries = load_queries()

    for item in queries:
        if item["case_type"] == "out_of_corpus":
            continue
        assert item["expected_answerable"] is True
        assert isinstance(item["expected_source"], str) and item["expected_source"]
        assert item["expected_source"] in item["expected_sources"]
        assert isinstance(item["expected_source_group"], str)
        assert item["expected_source_group"]
        assert item["expected_keywords"]
