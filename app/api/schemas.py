from pydantic import BaseModel, Field, field_validator


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query must not be empty")
        return value


class RetrievedChunk(BaseModel):
    chunk_id: str
    score: float
    content: str
    source: str
    file_type: str
    page: int | None = None


class RetrieveResponse(BaseModel):
    query: str
    top_k: int
    results: list[RetrievedChunk]


class ChatRequest(RetrieveRequest):
    pass


class ChatResponse(BaseModel):
    query: str
    answer: str
    retrieved_chunks: list[RetrievedChunk]
