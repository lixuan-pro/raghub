from app.llm.client_factory import get_llm_client
from app.llm.mock_client import NO_ANSWER_TEXT
from app.prompts.rag_prompt import build_rag_prompt
from app.services.retrieve_service import retrieve_chunks


MIN_RETRIEVAL_SCORE = 0.2
REASON_NO_CHUNKS = "no_retrieved_chunks"
REASON_LOW_SCORE = "retrieval_score_below_threshold"
REASON_EVIDENCE_FOUND = "retrieval_evidence_found"
REASON_QUERY_OUT_OF_SCOPE = "query_out_of_project_scope"

OUT_OF_SCOPE_KEYWORDS = (
    "手机号",
    "手机号码",
    "电话",
    "微信",
    "qq",
    "住址",
    "身份证",
    "明天线上用户量",
    "线上用户量",
    "未来用户量",
    "收入",
    "融资金额",
    "公司内部数据",
)


def is_query_out_of_project_scope(query: str) -> bool:
    normalized_query = query.lower()

    return any(
        keyword.lower() in normalized_query
        for keyword in OUT_OF_SCOPE_KEYWORDS
    )


def assess_answerability(query: str, chunks: list[dict]) -> tuple[bool, str]:
    if not chunks:
        return False, REASON_NO_CHUNKS

    if is_query_out_of_project_scope(query):
        return False, REASON_QUERY_OUT_OF_SCOPE

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
    is_answerable, reason = assess_answerability(query=query, chunks=chunks)

    if is_answerable:
        prompt = build_rag_prompt(query=query, chunks=chunks)
        answer = get_llm_client().generate(prompt)
    else:
        answer = NO_ANSWER_TEXT

    return {
        "query": query,
        "answer": answer,
        "is_answerable": is_answerable,
        "reason": reason,
        "sources": build_sources(chunks) if is_answerable else [],
        "retrieved_chunks": chunks,
    }
