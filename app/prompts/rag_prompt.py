def build_rag_prompt(query: str, chunks: list[dict]) -> str:
    context_lines: list[str] = []

    for index, chunk in enumerate(chunks, start=1):
        content = (chunk.get("content") or "").strip()
        source = chunk.get("source") or ""
        page = chunk.get("page")
        context_lines.append(
            f"[{index}] source={source}, page={page}\n{content}"
        )

    context = "\n\n".join(context_lines) if context_lines else "无可用检索片段。"

    return (
        "你是 RAGHub 的问答助手。\n"
        "只能基于给定资料回答用户问题。\n"
        "如果资料不足，请明确说明资料不足，无法基于当前文档回答。\n\n"
        f"用户问题：{query}\n\n"
        f"检索资料：\n{context}\n\n"
        "请给出简洁回答。"
    )
