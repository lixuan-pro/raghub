import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.services.rag_service import generate_chat_response


def main() -> None:
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("未检测到 DEEPSEEK_API_KEY，已跳过真实 DeepSeek 调用。")
        print("如需运行，请在本地环境配置 DEEPSEEK_API_KEY，并确认 LLM_PROVIDER=deepseek。")
        return

    os.environ["LLM_PROVIDER"] = "deepseek"
    os.environ.setdefault("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    os.environ.setdefault("DEEPSEEK_MODEL", "deepseek-v4-flash")

    query = "RAGHub 当前支持哪些文档处理能力？"
    top_k = 3
    response = generate_chat_response(query=query, top_k=top_k)

    print(f"query: {response['query']}")
    print(f"is_answerable: {response['is_answerable']}")
    print(f"reason: {response['reason']}")
    print("answer:")
    print(response["answer"])
    print("-" * 80)
    print("sources:")

    for rank, item in enumerate(response["sources"], start=1):
        print(f"rank: {rank}")
        print(f"chunk_id: {item['chunk_id']}")
        print(f"score: {item['score']:.4f}")
        print(f"source: {item['source']}")
        print(f"file_type: {item['file_type']}")
        print(f"page: {item['page']}")
        print(f"content_preview: {item['content_preview']}")
        print("-" * 80)


if __name__ == "__main__":
    main()
