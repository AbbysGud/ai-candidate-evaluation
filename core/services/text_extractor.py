from io import BytesIO
from pathlib import Path
from typing import IO, Union

from docx import Document as DocxDocument
from pypdf import PdfReader

try:
    from docx import Document as DocxDocument

    HAS_DOCX = True
except Exception:
    HAS_DOCX = False


FileLike = Union[str, Path, IO[bytes]]  # noqa: UP007


def _ensure_bytesio(src: FileLike) -> BytesIO:
    if isinstance(src, (str, Path)):
        with open(src, "rb") as f:
            return BytesIO(f.read())
    data = src.read()  # type: ignore[attr-defined]
    return BytesIO(data)


def extract_text_from_pdf(src: FileLike) -> str:
    bio = _ensure_bytesio(src)
    reader = PdfReader(bio)
    out = []
    for page in reader.pages:
        out.append(page.extract_text() or "")
    return "\n".join(out).strip()


def extract_text_from_docx(src: FileLike) -> str:
    bio = _ensure_bytesio(src)
    doc = DocxDocument(bio)
    paras = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(paras).strip()


def extract_text_auto(src: FileLike, mime: str) -> str:
    m = (mime or "").lower()
    if "pdf" in m:
        return extract_text_from_pdf(src)
    if "word" in m or m.endswith("officedocument.wordprocessingml.document"):
        return extract_text_from_docx(src)
    if isinstance(src, (str, Path)):
        try:
            return Path(src).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
    try:
        return _ensure_bytesio(src).getvalue().decode("utf-8", errors="ignore")
    except Exception:
        return ""
