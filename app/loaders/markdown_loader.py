from pathlib import Path

from app.models.document import Document


def load_markdown(path: str | Path) -> str:
    """Load text content from a Markdown file."""
    return Path(path).read_text(encoding="utf-8")


def load_markdown_documents(path: str | Path) -> list[Document]:
    """Load a Markdown file and wrap it as a Document list."""
    content = load_markdown(path)

    return [
        Document(
            content=content,
            source=str(path),
            file_type="md",
            page=None,
        )
    ]
