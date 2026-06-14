from fastapi.testclient import TestClient

import app.api.retrieve as retrieve_api
from app.main import app


client = TestClient(app)


def test_retrieve_returns_top_k_chunks(monkeypatch):
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

    monkeypatch.setattr(retrieve_api, "retrieve_chunks", fake_retrieve_chunks)

    response = client.post(
        "/retrieve",
        json={"query": "What document processing features does RAGHub support?", "top_k": 3},
    )

    assert response.status_code == 200

    body = response.json()
    assert body["query"] == "What document processing features does RAGHub support?"
    assert body["top_k"] == 3
    assert "results" in body
    assert isinstance(body["results"], list)

    result = body["results"][0]
    for field in ("chunk_id", "score", "content", "source", "file_type", "page"):
        assert field in result


def test_retrieve_rejects_empty_query():
    response = client.post("/retrieve", json={"query": "", "top_k": 3})

    assert response.status_code == 422


def test_retrieve_rejects_blank_query():
    response = client.post("/retrieve", json={"query": "   ", "top_k": 3})

    assert response.status_code == 422


def test_retrieve_rejects_top_k_above_limit():
    response = client.post("/retrieve", json={"query": "RAGHub", "top_k": 11})

    assert response.status_code == 422
