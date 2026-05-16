from app.loaders.pdf_loader import load_pdf_documents
from app.loaders.txt_loader import load_txt_documents
from app.models.document import Document


def test_load_txt_documents_returns_document_list():
    documents = load_txt_documents("data/raw/sample.txt")

    assert isinstance(documents, list)
    assert len(documents) == 1

    document = documents[0]
    assert isinstance(document, Document)
    assert "RAGHub" in document.content
    assert "sample.txt" in document.source
    assert document.file_type == "txt"
    assert document.page is None


def test_load_pdf_documents_returns_document_list_with_pages():
    documents = load_pdf_documents("data/raw/sample.pdf")

    assert isinstance(documents, list)
    assert len(documents) >= 1

    document = documents[0]
    assert isinstance(document, Document)
    assert "RAGHub" in document.content
    assert "sample.pdf" in document.source
    assert document.file_type == "pdf"
    assert document.page == 1