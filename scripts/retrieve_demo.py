import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.retrievers.vector_retriever import search_top_k


def main() -> None:
    query = "RAGHub 当前支持哪些文档处理能力？"
    top_k = 3

    results = search_top_k(query=query, top_k=top_k)

    print(f"query: {query}")
    print(f"top_k: {top_k}")
    print("-" * 80)

    for rank, item in enumerate(results, start=1):
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