from app.loaders.pdf_loader import load_pdf


def test_load_pdf_reads_sample_file_by_pages():
    pages = load_pdf("data/raw/sample.pdf")

    assert isinstance(pages, list)
    assert len(pages) >= 1

    text = "\n".join(pages)
    assert "RAGHub" in text
    assert "PDF loader" in text
    assert "page-based PDF text extraction" in text

