from fastapi.testclient import TestClient

import app.services.rag_service as rag_service
from app.main import app


client = TestClient(app)


def make_chunk(score: float = 0.83) -> dict:
    return {
        "chunk_id": "0",
        "score": score,
        "content": "RAGHub supports TXT and PDF loading.",
        "source": "data/raw/sample.txt",
        "file_type": "txt",
        "page": None,
    }


def test_chat_returns_answer_sources_and_retrieved_chunks(monkeypatch):
    class FakeLLMClient:
        def generate(self, prompt: str) -> str:
            return "fake llm answer"

    def fake_retrieve_chunks(query: str, top_k: int = 3):
        return [make_chunk(score=0.83)]

    monkeypatch.setattr(rag_service, "retrieve_chunks", fake_retrieve_chunks)
    monkeypatch.setattr(rag_service, "get_llm_client", lambda: FakeLLMClient())

    response = client.post(
        "/chat",
        json={"query": "What document processing features does RAGHub support?", "top_k": 3},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["query"] == "What document processing features does RAGHub support?"
    assert body["is_answerable"] is True
    assert body["reason"] == "retrieval_evidence_found"
    assert "answer" in body
    assert "retrieved_chunks" in body
    assert "sources" in body
    assert isinstance(body["retrieved_chunks"], list)
    assert isinstance(body["sources"], list)

    result = body["retrieved_chunks"][0]
    for field in ("chunk_id", "score", "content", "source", "file_type", "page"):
        assert field in result

    source = body["sources"][0]
    for field in ("chunk_id", "source", "file_type", "page", "score", "content_preview"):
        assert field in source

    assert source["content_preview"] == "RAGHub supports TXT and PDF loading."


def test_chat_calls_llm_when_answerable(monkeypatch):
    class FakeLLMClient:
        def generate(self, prompt: str) -> str:
            return "fake llm answer"

    def fake_retrieve_chunks(query: str, top_k: int = 3):
        return [make_chunk(score=0.83)]

    monkeypatch.setattr(rag_service, "retrieve_chunks", fake_retrieve_chunks)
    monkeypatch.setattr(rag_service, "get_llm_client", lambda: FakeLLMClient())

    response = client.post("/chat", json={"query": "RAGHub", "top_k": 3})

    assert response.status_code == 200
    assert response.json()["answer"] == "fake llm answer"


def test_chat_rejects_empty_query():
    response = client.post("/chat", json={"query": "", "top_k": 3})

    assert response.status_code == 422


def test_chat_rejects_top_k_above_limit():
    response = client.post("/chat", json={"query": "RAGHub", "top_k": 11})

    assert response.status_code == 422


def test_chat_returns_no_answer_when_no_chunks(monkeypatch):
    def fail_get_llm_client():
        raise AssertionError("LLM client should not be called")

    def fake_retrieve_chunks(query: str, top_k: int = 3):
        return []

    monkeypatch.setattr(rag_service, "retrieve_chunks", fake_retrieve_chunks)
    monkeypatch.setattr(rag_service, "get_llm_client", fail_get_llm_client)

    response = client.post("/chat", json={"query": "Unknown topic", "top_k": 3})

    assert response.status_code == 200

    body = response.json()
    assert body["is_answerable"] is False
    assert body["reason"] == "no_retrieved_chunks"
    assert body["sources"] == []
    assert body["retrieved_chunks"] == []
    assert body["answer"]


def test_chat_returns_no_answer_when_score_below_threshold(monkeypatch):
    def fail_get_llm_client():
        raise AssertionError("LLM client should not be called")

    def fake_retrieve_chunks(query: str, top_k: int = 3):
        return [make_chunk(score=0.05)]

    monkeypatch.setattr(rag_service, "retrieve_chunks", fake_retrieve_chunks)
    monkeypatch.setattr(rag_service, "get_llm_client", fail_get_llm_client)

    response = client.post("/chat", json={"query": "Weakly related question", "top_k": 3})

    assert response.status_code == 200

    body = response.json()
    assert body["is_answerable"] is False
    assert body["reason"] == "retrieval_score_below_threshold"
    assert body["sources"] == []
    assert len(body["retrieved_chunks"]) == 1
    assert body["answer"]
