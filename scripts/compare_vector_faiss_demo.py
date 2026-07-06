import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from app.retrievers.faiss_retriever import FAISSRetriever  # noqa: E402
from app.retrievers.vector_retriever import VectorRetriever  # noqa: E402


def print_results(label: str, results: list[dict]) -> None:
    print(label)
    print("-" * 80)

    for rank, item in enumerate(results, start=1):
        preview = item["content"][:160].replace("\n", " ")
        print(
            f"{rank}. chunk_id={item['chunk_id']} "
            f"score={item['score']:.4f} "
            f"source={item['source']} "
            f"page={item['page']}"
        )
        print(f"   {preview}")

    print()


def main() -> None:
    query = "RAGHub 的 /retrieve 接口返回哪些字段？"
    top_k = 3

    vector_results = VectorRetriever().search(query=query, top_k=top_k)
    faiss_results = FAISSRetriever().search(query=query, top_k=top_k)

    print("RAGHub vector vs FAISS retrieval demo")
    print(f"query: {query}")
    print(f"top_k: {top_k}")
    print("FAISS score: inner product over the same normalized chunk embeddings.")
    print()
    print_results("vector", vector_results)
    print_results("faiss", faiss_results)


if __name__ == "__main__":
    main()
