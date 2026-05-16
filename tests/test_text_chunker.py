from app.models.document import Document
from app.processors.text_chunker import chunk_documents, chunk_text


def test_chunk_text_splits_long_text():
    text = "abcdefghijklmnopqrstuvwxyz"

    chunks = chunk_text(text, chunk_size=10, overlap=2)

    assert isinstance(chunks, list)
    assert len(chunks) > 1
    assert all(len(chunk) <= 10 for chunk in chunks)


def test_chunk_text_keeps_overlap():
    text = "abcdefghijklmnopqrstuvwxyz"

    chunks = chunk_text(text, chunk_size=10, overlap=2)

    assert chunks[0][-2:] == chunks[1][:2]


def test_chunk_text_returns_empty_list_for_empty_text():
    chunks = chunk_text("", chunk_size=10, overlap=2)

    assert chunks == []


def test_chunk_documents_returns_document_chunks():
    documents = [
        Document(
            content="abcdefghijklmnopqrstuvwxyz",
            source="data/raw/sample.txt",
            file_type="txt",
            page=None,
        )
    ]

    chunks = chunk_documents(documents, chunk_size=10, overlap=2)

    assert isinstance(chunks, list)
    assert len(chunks) > 1
    assert all(isinstance(chunk, Document) for chunk in chunks)
    assert all(len(chunk.content) <= 10 for chunk in chunks)

    first_chunk = chunks[0]
    assert first_chunk.source == "data/raw/sample.txt"
    assert first_chunk.file_type == "txt"
    assert first_chunk.page is None