from fastapi.testclient import TestClient

import app.services.rag_service as rag_service
from app.main import app


client = TestClient(app)


def test_chat_returns_answer_and_retrieved_chunks(monkeypatch):
    def fake_retrieve_chunks(query: str, top_k: int = 3):
        return [
            {
                "chunk_id": "0",
                "score": 0.83,
                "content": "RAGHub supports TXT and PDF loading.",
                "source": "data/raw/sample.txt",
                "file_type": "txt",
                "page": None,
            }
        ]

    monkeypatch.setattr(rag_service, "retrieve_chunks", fake_retrieve_chunks)

    response = client.post(
        "/chat",
        json={"query": "What document processing features does RAGHub support?", "top_k": 3},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["query"] == "What document processing features does RAGHub support?"
    assert "answer" in body
    assert "基于检索片段" in body["answer"]
    assert "retrieved_chunks" in body
    assert isinstance(body["retrieved_chunks"], list)

    result = body["retrieved_chunks"][0]
    for field in ("chunk_id", "score", "content", "source", "file_type", "page"):
        assert field in result


def test_chat_rejects_empty_query():
    response = client.post("/chat", json={"query": "", "top_k": 3})

    assert response.status_code == 422


def test_chat_rejects_top_k_above_limit():
    response = client.post("/chat", json={"query": "RAGHub", "top_k": 11})

    assert response.status_code == 422


def test_chat_returns_insufficient_answer_when_no_chunks(monkeypatch):
    def fake_retrieve_chunks(query: str, top_k: int = 3):
        return []

    monkeypatch.setattr(rag_service, "retrieve_chunks", fake_retrieve_chunks)

    response = client.post("/chat", json={"query": "Unknown topic", "top_k": 3})

    assert response.status_code == 200

    body = response.json()
    assert body["retrieved_chunks"] == []
    assert "资料不足" in body["answer"]
