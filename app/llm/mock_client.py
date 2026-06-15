NO_ANSWER_TEXT = "当前知识库中没有找到足够依据回答该问题。"


def generate_mock_answer(
    prompt: str,
    chunks: list[dict],
    is_answerable: bool = True,
    reason: str = "",
) -> str:
    if not is_answerable:
        return NO_ANSWER_TEXT

    valid_chunks = [
        chunk for chunk in chunks if (chunk.get("content") or "").strip()
    ]

    if not valid_chunks:
        return NO_ANSWER_TEXT

    first_content = valid_chunks[0]["content"].strip()
    summary = first_content[:160]

    return (
        "这是基于检索片段生成的简化回答："
        f"{summary}"
    )
