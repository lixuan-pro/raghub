import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.services.rag_service import generate_chat_response


def main() -> None:
    query = "RAGHub 当前支持哪些文档处理能力？"
    top_k = 3

    response = generate_chat_response(query=query, top_k=top_k)

    print(f"query: {response['query']}")
    print("answer:")
    print(response["answer"])
    print("-" * 80)
    print("retrieved_chunks:")

    for rank, item in enumerate(response["retrieved_chunks"], start=1):
        print(f"rank: {rank}")
        print(f"chunk_id: {item['chunk_id']}")
        print(f"score: {item['score']:.4f}")
        print(f"source: {item['source']}")
        print(f"file_type: {item['file_type']}")
        print(f"page: {item['page']}")
        print("content:")
        print(item["content"][:300])
        print("-" * 80)


if __name__ == "__main__":
    main()
