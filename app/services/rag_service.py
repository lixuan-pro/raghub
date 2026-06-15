from app.llm.mock_client import generate_mock_answer
from app.prompts.rag_prompt import build_rag_prompt
from app.services.retrieve_service import retrieve_chunks


MIN_RETRIEVAL_SCORE = 0.2
REASON_NO_CHUNKS = "no_retrieved_chunks"
REASON_LOW_SCORE = "retrieval_score_below_threshold"
REASON_EVIDENCE_FOUND = "retrieval_evidence_found"


def assess_answerability(chunks: list[dict]) -> tuple[bool, str]:
    if not chunks:
        return False, REASON_NO_CHUNKS

    top_score = float(chunks[0].get("score") or 0)
    if top_score < MIN_RETRIEVAL_SCORE:
        return False, REASON_LOW_SCORE

    return True, REASON_EVIDENCE_FOUND


def build_sources(chunks: list[dict]) -> list[dict]:
    sources: list[dict] = []

    for chunk in chunks:
        content = (chunk.get("content") or "").strip()
        sources.append(
            {
                "chunk_id": str(chunk.get("chunk_id")),
                "source": chunk.get("source") or "",
                "file_type": chunk.get("file_type") or "",
                "page": chunk.get("page"),
                "score": float(chunk.get("score") or 0),
                "content_preview": content[:120],
            }
        )

    return sources


def generate_chat_response(query: str, top_k: int = 3) -> dict:
    chunks = retrieve_chunks(query=query, top_k=top_k)
    is_answerable, reason = assess_answerability(chunks)
    prompt = build_rag_prompt(query=query, chunks=chunks)
    answer = generate_mock_answer(
        prompt=prompt,
        chunks=chunks,
        is_answerable=is_answerable,
        reason=reason,
    )

    return {
        "query": query,
        "answer": answer,
        "is_answerable": is_answerable,
        "reason": reason,
        "sources": build_sources(chunks) if is_answerable else [],
        "retrieved_chunks": chunks,
    }
