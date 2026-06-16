import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.loaders.markdown_loader import load_markdown_documents
from app.loaders.pdf_loader import load_pdf_documents
from app.loaders.txt_loader import load_txt_documents
from app.processors.text_chunker import chunk_documents


PROJECT_MARKDOWN_PATHS = [
    ROOT_DIR / "README.md",
    ROOT_DIR / "docs/raghub_v0_2_scope.md",
    ROOT_DIR / "docs/problems_and_solutions.md",
    ROOT_DIR / "eval/bad_cases.md",
    ROOT_DIR / "eval/llm_answer_review.md",
]


CHUNK_SIZE = 500
CHUNK_OVERLAP = 80


def normalize_source(source: str) -> str:
    """Convert absolute source path to project-relative path when possible."""
    source_path = Path(source).resolve()

    try:
        return str(source_path.relative_to(ROOT_DIR)).replace("\\", "/")
    except ValueError:
        return source


def document_to_record(document, chunk_id: int) -> dict:
    """Convert a Document object to a JSONL record."""
    return {
        "chunk_id": chunk_id,
        "content": document.content,
        "source": normalize_source(document.source),
        "file_type": document.file_type,
        "page": document.page,
    }


def load_project_markdown_documents() -> list:
    documents = []

    for path in PROJECT_MARKDOWN_PATHS:
        if not path.exists():
            raise FileNotFoundError(f"Markdown source not found: {path}")
        documents.extend(load_markdown_documents(path))

    return documents


def main() -> None:
    txt_path = ROOT_DIR / "data/raw/sample.txt"
    pdf_path = ROOT_DIR / "data/raw/sample.pdf"
    output_path = ROOT_DIR / "data/processed/chunks_preview.jsonl"

    txt_documents = load_txt_documents(str(txt_path))
    pdf_documents = load_pdf_documents(str(pdf_path))
    markdown_documents = load_project_markdown_documents()

    documents = txt_documents + pdf_documents + markdown_documents
    chunks = chunk_documents(
        documents,
        chunk_size=CHUNK_SIZE,
        overlap=CHUNK_OVERLAP,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for chunk_id, chunk in enumerate(chunks):
            record = document_to_record(chunk, chunk_id=chunk_id)
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"txt documents: {len(txt_documents)}")
    print(f"pdf documents: {len(pdf_documents)}")
    print(f"markdown documents: {len(markdown_documents)}")
    print(f"chunks: {len(chunks)}")
    print(f"chunk_size: {CHUNK_SIZE}")
    print(f"chunk_overlap: {CHUNK_OVERLAP}")
    print(f"output: {output_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
