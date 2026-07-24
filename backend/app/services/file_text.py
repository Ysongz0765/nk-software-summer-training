from __future__ import annotations

from pathlib import Path

from app.core.exceptions import UnsupportedFileTypeError
from app.services.template.docx import read_template_text

TEXT_SUFFIXES = {".txt"}
DOCUMENT_SUFFIXES = {".docx", ".xlsx", ".pdf"}
READABLE_SUFFIXES = TEXT_SUFFIXES | DOCUMENT_SUFFIXES
TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "gb18030")


def extract_file_text(file_path: str | Path) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return _read_plain_text(path)
    if suffix in DOCUMENT_SUFFIXES:
        return read_template_text(path)
    raise UnsupportedFileTypeError(
        "only txt, docx, xlsx and pdf files are supported for text extraction"
    )


def _read_plain_text(path: Path) -> str:
    for encoding in TEXT_ENCODINGS:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")
