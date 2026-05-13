from pathlib import Path


def load_txt(path: str) -> str:
    """Load text content from a TXT file."""
    return Path(path).read_text(encoding="utf-8")