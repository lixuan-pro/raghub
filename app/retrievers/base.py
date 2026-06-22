from typing import Protocol


class BaseRetriever(Protocol):
    def search(self, query: str, top_k: int = 3) -> list[dict]:
        ...
