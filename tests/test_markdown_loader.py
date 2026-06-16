from app.loaders.markdown_loader import load_markdown, load_markdown_documents
from app.models.document import Document


def test_load_markdown_reads_readme():
    content = load_markdown("README.md")

    assert isinstance(content, str)
    assert "RAGHub" in content
    assert "/chat" in content


def test_load_markdown_documents_returns_document_list():
    documents = load_markdown_documents("README.md")

    assert isinstance(documents, list)
    assert len(documents) == 1

    document = documents[0]
    assert isinstance(document, Document)
    assert "RAGHub" in document.content
    assert "README.md" in document.source
    assert document.file_type == "md"
    assert document.page is None
