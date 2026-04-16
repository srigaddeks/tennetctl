from __future__ import annotations

"""
Document text chunker for copilot attachment RAG.

Supports plain text, markdown, PDF, DOCX, XLSX, CSV, JSON, HTML.
Chunks by paragraph/sentence boundary with configurable overlap.

Supported MIME types:
  text/plain, text/markdown, text/csv, text/html (stripped)
  application/pdf  (requires pypdf)
  application/json
  application/vnd.openxmlformats-officedocument.wordprocessingml.document (python-docx)
  application/vnd.openxmlformats-officedocument.spreadsheetml.sheet (openpyxl)
  image/*  — returns empty string (images require vision model, not text RAG)
"""

import re
from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.memory.chunker")

CHUNK_SIZE = 600       # target characters per chunk
CHUNK_OVERLAP = 100    # overlap characters between chunks
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB hard limit
MAX_CHUNKS = 400       # safety cap on chunks per document


def extract_text(file_bytes: bytes, content_type: str, filename: str) -> str:
    """
    Extract plain text from file bytes based on content type.
    Returns empty string on failure (caller decides what to do).
    """
    ct = content_type.lower().split(";")[0].strip()
    fname = filename.lower()

    # ── Plain text variants ───────────────────────────────────────────────
    if ct in ("text/plain", "text/markdown", "text/csv", "text/x-csv"):
        return _decode(file_bytes)

    if ct == "application/json" or fname.endswith(".json"):
        return _decode(file_bytes)

    # ── HTML — strip tags ─────────────────────────────────────────────────
    if ct == "text/html" or fname.endswith(".html"):
        raw = _decode(file_bytes)
        return re.sub(r"<[^>]+>", " ", raw)

    # ── PDF ───────────────────────────────────────────────────────────────
    if ct == "application/pdf" or fname.endswith(".pdf"):
        return _extract_pdf(file_bytes)

    # ── DOCX ──────────────────────────────────────────────────────────────
    if (ct == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            or fname.endswith(".docx")):
        return _extract_docx(file_bytes)

    # ── XLSX / Excel ─────────────────────────────────────────────────────
    if (ct in (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        ) or fname.endswith((".xlsx", ".xls"))):
        return _extract_xlsx(file_bytes)

    # ── Images — not extractable as text ─────────────────────────────────
    if ct.startswith("image/") or fname.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")):
        _logger.info("Image file %s cannot be text-extracted for RAG", filename)
        return ""

    # ── Fallback: try UTF-8 decode ────────────────────────────────────────
    _logger.warning("Unknown content type %s for %s — attempting raw decode", ct, filename)
    return _decode(file_bytes)


def chunk_text(text: str) -> list[str]:
    """
    Split text into overlapping chunks by paragraph/sentence boundaries.
    Returns list of chunk strings (max MAX_CHUNKS items).
    """
    # Normalise whitespace
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    if not text:
        return []

    # Split on paragraph breaks first
    paragraphs = re.split(r"\n\n+", text)
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If the paragraph alone exceeds CHUNK_SIZE, split it further by sentences
        if len(para) > CHUNK_SIZE:
            sentences = _split_sentences(para)
            for sent in sentences:
                if len(current) + len(sent) + 1 > CHUNK_SIZE and current:
                    chunks.append(current.strip())
                    # Overlap: keep last CHUNK_OVERLAP chars
                    current = current[-CHUNK_OVERLAP:] + " " + sent
                else:
                    current = current + " " + sent if current else sent
        else:
            if len(current) + len(para) + 2 > CHUNK_SIZE and current:
                chunks.append(current.strip())
                current = current[-CHUNK_OVERLAP:] + "\n\n" + para
            else:
                current = current + "\n\n" + para if current else para

    if current.strip():
        chunks.append(current.strip())

    return chunks[:MAX_CHUNKS]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _decode(data: bytes) -> str:
    for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, ValueError):
            continue
    return data.decode("utf-8", errors="replace")


def _split_sentences(text: str) -> list[str]:
    """Rough sentence splitter (no NLTK dependency)."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p for p in parts if p.strip()]


def _extract_pdf(file_bytes: bytes) -> str:
    try:
        import io
        from pypdf import PdfReader  # optional dep
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
        return "\n\n".join(pages)
    except ImportError:
        _logger.warning("pypdf not installed — cannot extract PDF text")
        return ""
    except Exception as exc:
        _logger.warning("PDF extraction failed: %s", exc)
        return ""


def _extract_docx(file_bytes: bytes) -> str:
    try:
        import io
        from docx import Document  # python-docx
        doc = Document(io.BytesIO(file_bytes))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        _logger.warning("python-docx not installed — cannot extract DOCX text")
        return ""
    except Exception as exc:
        _logger.warning("DOCX extraction failed: %s", exc)
        return ""


def _extract_xlsx(file_bytes: bytes) -> str:
    """Extract text from Excel XLSX files using openpyxl."""
    try:
        import io
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
        parts: list[str] = []
        for sheet in wb.worksheets:
            sheet_rows: list[str] = []
            for row in sheet.iter_rows(values_only=True):
                cells = [str(c) if c is not None else "" for c in row]
                row_text = "\t".join(cells).rstrip()
                if any(c for c in cells):
                    sheet_rows.append(row_text)
            if sheet_rows:
                parts.append(f"Sheet: {sheet.title}\n" + "\n".join(sheet_rows))
        wb.close()
        return "\n\n".join(parts)
    except Exception as exc:
        _logger.warning("XLSX extraction failed: %s", exc)
        return ""
