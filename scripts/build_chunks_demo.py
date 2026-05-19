import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.loaders.pdf_loader import load_pdf_documents
from app.loaders.txt_loader import load_txt_documents
from app.processors.text_chunker import chunk_documents


def normalize_source(source: str) -> str:
    """Convert absolute source path to project-relative path when possible."""
    source_path = Path(source).resolve()

    try:
        return str(source_path.relative_to(ROOT_DIR)).replace("\\", "/")
    except ValueError:
        return source


def document_to_record(document) -> dict:
    """Convert a Document object to a JSONL record."""
    return {
        "content": document.content,
        "source": normalize_source(document.source),
        "file_type": document.file_type,
        "page": document.page,
    }


def main() -> None:
    txt_path = ROOT_DIR / "data/raw/sample.txt"
    pdf_path = ROOT_DIR / "data/raw/sample.pdf"
    output_path = ROOT_DIR / "data/processed/chunks_preview.jsonl"

    txt_documents = load_txt_documents(str(txt_path))
    pdf_documents = load_pdf_documents(str(pdf_path))

    documents = txt_documents + pdf_documents
    chunks = chunk_documents(documents, chunk_size=50, overlap=10)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            record = document_to_record(chunk)
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"txt documents: {len(txt_documents)}")
    print(f"pdf documents: {len(pdf_documents)}")
    print(f"chunks: {len(chunks)}")
    print(f"output: {output_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()