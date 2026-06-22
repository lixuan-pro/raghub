import math
import re
from collections import Counter
from pathlib import Path

from app.retrievers.vector_retriever import DEFAULT_CHUNKS_PATH, load_jsonl_chunks


TOKEN_PATTERN = re.compile(
    r"/[a-z0-9_./-]+"
    r"|\.[a-z][a-z0-9_-]*"
    r"|[a-z0-9]+(?:_[a-z0-9]+)+"
    r"|[a-z0-9]+(?:-[a-z0-9]+)*"
    r"|[\u4e00-\u9fff]+",
    re.IGNORECASE,
)
ASCII_TOKEN_PATTERN = re.compile(r"^[a-z0-9_./-]+$")
CJK_PATTERN = re.compile(r"^[\u4e00-\u9fff]+$")


def tokenize(text: str) -> list[str]:
    if not text:
        return []

    raw_tokens: list[str] = []

    for match in TOKEN_PATTERN.finditer(text.lower()):
        token = match.group(0)

        if CJK_PATTERN.match(token):
            raw_tokens.extend(token)
            raw_tokens.extend(
                token[index : index + 2]
                for index in range(max(len(token) - 1, 0))
            )
            continue

        raw_tokens.append(token)

        if token.startswith("/"):
            raw_tokens.append(token.lstrip("/"))
        if token.startswith("."):
            raw_tokens.append(token.lstrip("."))

        for part in re.split(r"[/._-]+", token):
            if part:
                raw_tokens.append(part)

    phrase_tokens: list[str] = []
    simple_tokens = [
        token
        for token in raw_tokens
        if ASCII_TOKEN_PATTERN.match(token) and "/" not in token and "." not in token
    ]
    phrase_tokens.extend(
        f"{simple_tokens[index]}_{simple_tokens[index + 1]}"
        for index in range(max(len(simple_tokens) - 1, 0))
    )

    return raw_tokens + phrase_tokens


class BM25Retriever:
    def __init__(
        self,
        chunks_path: Path = DEFAULT_CHUNKS_PATH,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.chunks_path = chunks_path
        self.k1 = k1
        self.b = b
        self.chunks = load_jsonl_chunks(chunks_path)
        self.doc_tokens = [self._tokens_for_chunk(chunk) for chunk in self.chunks]
        self.doc_term_counts = [Counter(tokens) for tokens in self.doc_tokens]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_length = (
            sum(self.doc_lengths) / len(self.doc_lengths)
            if self.doc_lengths
            else 0
        )
        self.idf = self._build_idf()

    def _tokens_for_chunk(self, chunk: dict) -> list[str]:
        searchable_text = " ".join(
            str(part or "")
            for part in (
                chunk.get("content"),
                chunk.get("source"),
                chunk.get("file_type"),
            )
        )
        return tokenize(searchable_text)

    def _build_idf(self) -> dict[str, float]:
        doc_count = len(self.doc_tokens)
        document_frequency: Counter[str] = Counter()

        for tokens in self.doc_tokens:
            document_frequency.update(set(tokens))

        return {
            token: math.log(
                ((doc_count - frequency + 0.5) / (frequency + 0.5)) + 1
            )
            for token, frequency in document_frequency.items()
        }

    def _score(self, query_tokens: list[str], doc_index: int) -> float:
        if not query_tokens or self.avg_doc_length == 0:
            return 0.0

        term_counts = self.doc_term_counts[doc_index]
        doc_length = self.doc_lengths[doc_index]
        score = 0.0

        for token in query_tokens:
            term_frequency = term_counts.get(token, 0)
            if term_frequency == 0:
                continue

            idf = self.idf.get(token, 0.0)
            denominator = (
                term_frequency
                + self.k1
                * (1 - self.b + self.b * doc_length / self.avg_doc_length)
            )
            score += idf * (
                term_frequency * (self.k1 + 1)
            ) / denominator

        return score

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if not query or not query.strip():
            raise ValueError("query must not be empty")

        query_tokens = tokenize(query)
        scores = [
            self._score(query_tokens=query_tokens, doc_index=index)
            for index in range(len(self.chunks))
        ]

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )
        top_indices = ranked_indices[: min(top_k, len(ranked_indices))]

        results: list[dict] = []
        for index in top_indices:
            chunk = self.chunks[index]
            score = float(scores[index])
            results.append(
                {
                    "chunk_id": int(index),
                    "score": score,
                    "content": chunk.get("content", ""),
                    "source": chunk.get("source"),
                    "file_type": chunk.get("file_type"),
                    "page": chunk.get("page"),
                    "retrieval_score_detail": {
                        "bm25_score": score,
                    },
                }
            )

        return results
