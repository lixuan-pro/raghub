import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.retrievers.faiss_retriever import FAISSRetriever  # noqa: E402


def main() -> None:
    query = "RAGHub 当前支持哪些文档处理能力？"
    top_k = 3

    retriever = FAISSRetriever()
    results = retriever.search(query=query, top_k=top_k)

    print("RAGHub FAISS retrieval demo")
    print(f"query: {query}")
    print(f"top_k: {top_k}")
    print("score: FAISS inner product over normalized embeddings")
    print("-" * 80)

    for rank, item in enumerate(results, start=1):
        print(f"rank: {rank}")
        print(f"chunk_id: {item['chunk_id']}")
        print(f"score: {item['score']:.4f}")
        print(f"source: {item['source']}")
        print(f"file_type: {item['file_type']}")
        print(f"page: {item['page']}")
        print("content preview:")
        print(item["content"][:300].replace("\n", " "))
        print("-" * 80)


if __name__ == "__main__":
    main()
