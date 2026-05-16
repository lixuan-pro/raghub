from pathlib import Path

from app.models.document import Document


def load_txt(path: str) -> str:
    """Load text content from a TXT file."""
    return Path(path).read_text(encoding="utf-8")


def load_txt_documents(path: str) -> list[Document]:
    """Load a TXT file and wrap it as a Document list."""
    content = load_txt(path)

    return [
        Document(
            content=content,
            source=str(path),
            file_type="txt",
            page=None,
        )
    ]