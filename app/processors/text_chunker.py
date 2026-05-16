from app.models.document import Document


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into fixed-size chunks with overlap."""
    if not text:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def chunk_documents(
    documents: list[Document],
    chunk_size: int,
    overlap: int,
) -> list[Document]:
    """Split documents into smaller Document chunks."""
    chunked_documents: list[Document] = []

    for document in documents:
        chunks = chunk_text(document.content, chunk_size, overlap)

        for chunk in chunks:
            chunked_documents.append(
                Document(
                    content=chunk,
                    source=document.source,
                    file_type=document.file_type,
                    page=document.page,
                )
            )

    return chunked_documents