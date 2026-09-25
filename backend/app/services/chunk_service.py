import logging
from typing import TypedDict
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


class ChunkResult(TypedDict):
    chunk_id: str          # "{document_id}_p{page}_c{idx}" — globally unique
    document_id: str
    document_name: str
    page_number: int       # 1-indexed
    text: str
    chunk_index: int       # 0-indexed sequential across the whole document


def chunk_pages(
    pages: list[dict],
    document_id: str,
    document_name: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[ChunkResult]:
    """
    Split page-level text into overlapping chunks, preserving page provenance.

    Each chunk carries a unique chunk_id that encodes document, page, and
    position — enabling exact source citation later.

    Args:
        pages:         list of {page_number, text} dicts from pdf_service
        document_id:   MongoDB / ChromaDB document identifier
        document_name: human-readable filename (used in citations)
        chunk_size:    maximum characters per chunk
        overlap:       character overlap between consecutive chunks

    Returns:
        Ordered list of ChunkResult dicts.
    """
    chunks: list[ChunkResult] = []
    global_idx = 0

    for page in pages:
        page_num: int = page["page_number"]
        text: str = page["text"].strip()

        if not text:
            continue  # skip blank pages (e.g. image-only in scanned PDFs)

        start = 0
        page_chunk_idx = 0

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunk_id = f"{document_id}_p{page_num}_c{page_chunk_idx}"
                chunks.append(
                    ChunkResult(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        document_name=document_name,
                        page_number=page_num,
                        text=chunk_text,
                        chunk_index=global_idx,
                    )
                )
                global_idx += 1
                page_chunk_idx += 1

            start += chunk_size - overlap

    logger.info(
        "Chunked '%s': %d chunks from %d pages",
        document_name,
        len(chunks),
        len(pages),
    )
    return chunks


# ── Backward-compatibility shim ──────────────────────────────────────────────
# The /test-chunk route and /ingest route import chunk_text from this module.
# Kept intentionally so existing routes are not broken.

def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[str]:
    """
    Simple character-based chunker (legacy helper).
    Returns plain text strings without page metadata.
    Used by /test-chunk and /ingest debug routes.
    """
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunk = text[start : start + chunk_size]
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks