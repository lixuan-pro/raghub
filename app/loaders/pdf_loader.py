from pypdf import PdfReader


def load_pdf(path: str) -> list[str]:
    """Load text content from a PDF file page by page."""
    reader = PdfReader(path)

    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)

    return pages






