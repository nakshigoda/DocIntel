"""
upload.py — Document ingestion endpoint.

Pipeline:
  1. Validate file (type, size, PDF magic bytes)
  2. Save to disk with a UUID-prefixed safe filename
  3. Create MongoDB record  (status: "uploaded")
  4. Extract text per-page with PyMuPDF, clean it
  5. Detect scanned / image-based PDFs
  6. Chunk with page-level metadata (chunk_id, page_number, etc.)
  7. Generate embeddings (sentence_transformers, local, no API key)
  8. Persist chunks + embeddings in ChromaDB
  9. Update MongoDB record  (status: "processed" | "failed")
 10. Return a structured response
"""

import os
import re
import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import UPLOAD_DIR, MAX_FILE_SIZE_MB
from app.services.database import documents_collection
from app.services.pdf_service import extract_pages
from app.services.chunk_service import chunk_pages
from app.services.embedding_service import generate_embedding
from app.services.vector_service import upsert_chunks

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Upload"])

os.makedirs(UPLOAD_DIR, exist_ok=True)

_MAX_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def _safe_filename(name: str) -> str:
    """Strip path components and replace unsafe characters."""
    name = os.path.basename(name)
    name = re.sub(r"[^\w\-_\. ]", "_", name)
    return name.strip() or "document.pdf"


@router.post("/upload", summary="Upload and process a PDF document")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF, extract text, chunk it, embed it, and persist everything.

    Returns document_id, processing stats, and current status.
    """
    # ── 1. Validate ───────────────────────────────────────────────────────────
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    raw_content = await file.read()

    if len(raw_content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(raw_content) > _MAX_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds the {MAX_FILE_SIZE_MB} MB limit "
                   f"({len(raw_content) / 1024 / 1024:.1f} MB received)",
        )

    # Validate PDF magic bytes (%PDF header)
    if not raw_content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400, detail="File content does not appear to be a valid PDF"
        )

    # ── 2. Save to disk ───────────────────────────────────────────────────────
    doc_id = str(uuid.uuid4())
    safe_name = _safe_filename(file.filename)
    stored_filename = f"{doc_id}_{safe_name}"
    file_path = os.path.join(UPLOAD_DIR, stored_filename)

    with open(file_path, "wb") as fh:
        fh.write(raw_content)

    logger.info("Saved uploaded file: %s (%d bytes)", stored_filename, len(raw_content))

    # ── 3. Create initial MongoDB record ──────────────────────────────────────
    now = datetime.utcnow()
    doc_record = {
        "document_id":     doc_id,
        "filename":        file.filename,
        "stored_filename": stored_filename,
        "filepath":        file_path,
        "file_size_bytes": len(raw_content),
        "uploaded_at":     now,
        "status":          "uploaded",
        # These will be filled in after processing
        "page_count":      0,
        "word_count":      0,
        "character_count": 0,
        "chunk_count":     0,
        "is_scanned":      False,
        "processed_at":    None,
        "error":           None,
    }

    insert_result = documents_collection.insert_one(doc_record)
    mongo_id = str(insert_result.inserted_id)

    # ── 4–8. Processing pipeline ──────────────────────────────────────────────
    try:
        documents_collection.update_one(
            {"_id": insert_result.inserted_id},
            {"$set": {"status": "processing"}},
        )

        # Extract text per page
        extraction = extract_pages(file_path)
        pages = extraction["pages"]

        # Chunk with full metadata
        chunks = chunk_pages(
            pages=pages,
            document_id=doc_id,
            document_name=file.filename,
        )

        # Embed and store in ChromaDB
        chunk_count_stored = 0
        if chunks:
            embeddings = [generate_embedding(c["text"]) for c in chunks]
            chunk_count_stored = upsert_chunks(chunks, embeddings)

        # ── 9. Update MongoDB with final stats ────────────────────────────────
        documents_collection.update_one(
            {"_id": insert_result.inserted_id},
            {
                "$set": {
                    "status":          "processed",
                    "page_count":      extraction["page_count"],
                    "word_count":      extraction["word_count"],
                    "character_count": extraction["total_chars"],
                    "chunk_count":     chunk_count_stored,
                    "is_scanned":      extraction["is_scanned"],
                    "processed_at":    datetime.utcnow(),
                }
            },
        )

        logger.info(
            "Document '%s' processed: %d pages, %d chunks",
            file.filename,
            extraction["page_count"],
            chunk_count_stored,
        )

        # ── 10. Return response ───────────────────────────────────────────────
        message = "Document processed successfully."
        if extraction["is_scanned"]:
            message += (
                " Warning: this document appears to be scanned or image-based. "
                "OCR is not currently enabled, so extracted text may be sparse."
            )
        if chunk_count_stored == 0:
            message += " No text could be extracted — the document may be empty or image-only."

        return {
            "document_id":   doc_id,
            "mongo_id":      mongo_id,
            "filename":      file.filename,
            "status":        "processed",
            "page_count":    extraction["page_count"],
            "word_count":    extraction["word_count"],
            "character_count": extraction["total_chars"],
            "chunk_count":   chunk_count_stored,
            "is_scanned":    extraction["is_scanned"],
            "message":       message,
        }

    except Exception as exc:
        error_msg = str(exc)
        logger.error("Processing failed for '%s': %s", file.filename, error_msg)

        documents_collection.update_one(
            {"_id": insert_result.inserted_id},
            {"$set": {"status": "failed", "error": error_msg}},
        )

        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {error_msg}",
        )