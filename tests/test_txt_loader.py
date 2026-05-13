from app.loaders.txt_loader import load_txt


def test_load_txt_reads_sample_file():
    content = load_txt("data/raw/sample.txt")

    assert isinstance(content, str)
    assert "RAGHub" in content
    assert "document loading" in content