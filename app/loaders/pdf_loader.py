from pypdf import PdfReader

from app.models.document import Document


def load_pdf(path: str) -> list[str]:
    """Load text content from a PDF file page by page."""
    reader = PdfReader(path)

    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)

    return pages


def load_pdf_documents(path: str) -> list[Document]:
    """Load a PDF file and wrap each page as a Document."""
    pages = load_pdf(path)

    documents: list[Document] = []
    for index, content in enumerate(pages, start=1):
        documents.append(
            Document(
                content=content,
                source=str(path),
                file_type="pdf",
                page=index,
            )
        )

    return documents