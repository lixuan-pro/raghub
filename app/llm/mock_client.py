NO_ANSWER_TEXT = "当前知识库中没有找到足够依据回答该问题。"


class MockLLMClient:
    def generate(self, prompt: str) -> str:
        marker = "检索资料："
        context = prompt.split(marker, maxsplit=1)[-1].strip()
        context_lines = [line.strip() for line in context.splitlines() if line.strip()]
        content_lines = [
            line
            for line in context_lines
            if not line.startswith("[") and not line.startswith("请")
        ]
        summary = content_lines[0][:160] if content_lines else ""

        return f"这是基于检索片段生成的简化回答：{summary}"


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

    return MockLLMClient().generate(prompt)
