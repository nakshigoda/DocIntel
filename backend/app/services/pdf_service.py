import fitz  # PyMuPDF
import re
import logging
from typing import TypedDict
from app.config import OCR_TEXT_THRESHOLD

logger = logging.getLogger(__name__)


class PageResult(TypedDict):
    page_number: int   # 1-indexed
    text: str


class ExtractionResult(TypedDict):
    pages: list[PageResult]
    page_count: int
    total_chars: int
    word_count: int
    is_scanned: bool


def _clean_text(text: str) -> str:
    """
    Clean raw text extracted from a PDF page.

    Operations:
    - Fix hyphenated line-breaks that PDFs introduce mid-word (e.g. "infor-\nmation" → "information")
    - Collapse single newlines to spaces (preserves paragraph breaks = double newlines)
    - Collapse runs of spaces to a single space
    - Remove control characters (except \\n)
    - Strip leading / trailing whitespace
    """
    if not text:
        return ""

    # Normalize unicode / drop invalid bytes
    text = text.encode("utf-8", errors="ignore").decode("utf-8")

    # Rejoin words broken across lines with a hyphen (PDF line-wrap artefact)
    text = re.sub(r"-\n(\w)", r"\1", text)

    # Single newline → space (preserve double-newline paragraph breaks)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Collapse 3+ newlines to double newline
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces
    text = re.sub(r" {2,}", " ", text)

    # Remove control characters except newline (\n = 0x0A)
    text = re.sub(r"[\x00-\x09\x0b-\x1f\x7f]", "", text)

    return text.strip()


def extract_pages(pdf_path: str) -> ExtractionResult:
    """
    Extract and clean text from each page of a PDF, preserving page boundaries.

    Returns an ExtractionResult dict containing per-page text plus aggregate stats.
    If a page yields very little text (< OCR_TEXT_THRESHOLD chars), the document
    is flagged as potentially scanned. OCR is not currently enabled — a warning
    is logged and downstream code should handle empty pages gracefully.

    Raises:
        Exception: if the PDF cannot be opened or read.
    """
    doc = fitz.open(pdf_path)
    pages: list[PageResult] = []
    total_chars = 0

    for i, page in enumerate(doc):
        raw = page.get_text()
        cleaned = _clean_text(raw)
        total_chars += len(cleaned)
        pages.append({"page_number": i + 1, "text": cleaned})

    doc.close()

    page_count = len(pages)
    word_count = sum(len(p["text"].split()) for p in pages)
    avg_chars = total_chars / page_count if page_count > 0 else 0
    is_scanned = avg_chars < OCR_TEXT_THRESHOLD

    if is_scanned:
        logger.warning(
            "PDF '%s' appears to be scanned or image-based "
            "(avg %.0f chars/page, threshold %d). "
            "OCR is not currently enabled — extracted text may be empty. "
            "Architecture supports plugging in an OCR service later.",
            pdf_path,
            avg_chars,
            OCR_TEXT_THRESHOLD,
        )

    logger.info(
        "Extracted '%s': %d pages, %d chars, %d words, scanned=%s",
        pdf_path,
        page_count,
        total_chars,
        word_count,
        is_scanned,
    )

    return {
        "pages": pages,
        "page_count": page_count,
        "total_chars": total_chars,
        "word_count": word_count,
        "is_scanned": is_scanned,
    }