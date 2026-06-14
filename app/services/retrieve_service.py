from app.retrievers.vector_retriever import search_top_k


def retrieve_chunks(query: str, top_k: int = 3) -> list[dict]:
    results = search_top_k(query=query, top_k=top_k)

    return [
        {
            "chunk_id": str(item["chunk_id"]),
            "score": item["score"],
            "content": item["content"],
            "source": item.get("source") or "",
            "file_type": item.get("file_type") or "",
            "page": item["page"],
        }
        for item in results
    ]
