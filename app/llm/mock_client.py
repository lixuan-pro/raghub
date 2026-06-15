INSUFFICIENT_ANSWER = "资料不足，无法基于当前文档回答。"


def generate_mock_answer(prompt: str, chunks: list[dict]) -> str:
    valid_chunks = [
        chunk for chunk in chunks if (chunk.get("content") or "").strip()
    ]

    if not valid_chunks:
        return INSUFFICIENT_ANSWER

    first_content = valid_chunks[0]["content"].strip()
    summary = first_content[:160]

    return (
        "这是基于检索片段生成的简化回答："
        f"{summary}"
    )
