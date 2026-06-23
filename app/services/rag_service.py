from app.llm.client_factory import get_llm_client
from app.llm.mock_client import NO_ANSWER_TEXT
from app.prompts.rag_prompt import build_rag_prompt
from app.services.retrieve_service import retrieve_chunks


MIN_RETRIEVAL_SCORE = 0.2
REASON_NO_CHUNKS = "no_retrieved_chunks"
REASON_LOW_SCORE = "retrieval_score_below_threshold"
REASON_EVIDENCE_FOUND = "retrieval_evidence_found"
REASON_QUERY_OUT_OF_SCOPE = "query_out_of_project_scope"

PERSONAL_INFO_KEYWORDS = (
    "手机号",
    "手机号码",
    "电话",
    "微信",
    "qq",
    "身份证",
    "身份证号",
    "住址",
    "家庭住址",
)
AUTHOR_PRIVATE_KEYWORDS = (
    "作者",
    "维护者",
    "项目维护者",
    "开发者",
)
SECRET_VALUE_KEYWORDS = (
    "api_key",
    "api key",
    "token",
    "密钥",
    "secret",
    "password",
)
SECRET_DISCLOSURE_KEYWORDS = (
    "真实值",
    "真实 key",
    "真实 token",
    "直接告诉",
    "请输出",
    "输出",
    "明文",
    "完整值",
    "原始值",
)
FUTURE_PREDICTION_KEYWORDS = (
    "明天",
    "下周",
    "下个月",
    "未来",
    "下一次",
    "未发布版本",
)
FUTURE_TARGET_KEYWORDS = (
    "线上用户量",
    "未来用户量",
    "用户量",
    "qps",
    "峰值",
    "收入",
    "融资金额",
    "上线日期",
    "分数",
    "一定是多少",
)
REAL_TIME_KEYWORDS = (
    "当前实时",
    "实时",
    "最新",
    "现在",
    "今天",
)
INTERNAL_BUSINESS_KEYWORDS = (
    "公司内部数据",
    "内部数据",
    "真实客户",
    "客户 a",
    "内部合同",
    "合同金额",
    "员工薪资表",
    "薪资表",
    "未说明公司",
)
UNSUPPORTED_EXTERNAL_KNOWLEDGE_KEYWORDS = (
    "医疗诊断",
    "诊断方案",
    "处方",
    "治疗方案",
)


def _contains_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def classify_out_of_scope_query(query: str) -> str | None:
    normalized_query = query.lower()

    if _contains_any(normalized_query, AUTHOR_PRIVATE_KEYWORDS) and _contains_any(
        normalized_query,
        PERSONAL_INFO_KEYWORDS,
    ):
        return "author_private_info"

    if _contains_any(normalized_query, SECRET_VALUE_KEYWORDS) and _contains_any(
        normalized_query,
        SECRET_DISCLOSURE_KEYWORDS,
    ):
        return "privacy_personal_info"

    if _contains_any(normalized_query, FUTURE_PREDICTION_KEYWORDS) and _contains_any(
        normalized_query,
        FUTURE_TARGET_KEYWORDS,
    ):
        return "future_prediction"

    if _contains_any(normalized_query, REAL_TIME_KEYWORDS) and _contains_any(
        normalized_query,
        FUTURE_TARGET_KEYWORDS,
    ):
        return "real_time_external_fact"

    if _contains_any(normalized_query, INTERNAL_BUSINESS_KEYWORDS):
        return "internal_business_data"

    if _contains_any(normalized_query, UNSUPPORTED_EXTERNAL_KNOWLEDGE_KEYWORDS):
        return "unsupported_external_knowledge"

    if _contains_any(normalized_query, PERSONAL_INFO_KEYWORDS):
        return "privacy_personal_info"

    return None


def is_query_out_of_project_scope(query: str) -> bool:
    return classify_out_of_scope_query(query) is not None


def assess_answerability(query: str, chunks: list[dict]) -> tuple[bool, str]:
    if not chunks:
        return False, REASON_NO_CHUNKS

    out_of_scope_category = classify_out_of_scope_query(query)
    if out_of_scope_category:
        return False, f"{REASON_QUERY_OUT_OF_SCOPE}:{out_of_scope_category}"

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
