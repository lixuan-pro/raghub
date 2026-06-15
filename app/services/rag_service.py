from app.llm.mock_client import generate_mock_answer
from app.prompts.rag_prompt import build_rag_prompt
from app.services.retrieve_service import retrieve_chunks


def generate_chat_response(query: str, top_k: int = 3) -> dict:
    chunks = retrieve_chunks(query=query, top_k=top_k)
    prompt = build_rag_prompt(query=query, chunks=chunks)
    answer = generate_mock_answer(prompt=prompt, chunks=chunks)

    return {
        "query": query,
        "answer": answer,
        "retrieved_chunks": chunks,
    }
