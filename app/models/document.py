
from dataclasses import dataclass


@dataclass
class Document:
    content: str
    source: str
    file_type: str
    page: int | None = None
