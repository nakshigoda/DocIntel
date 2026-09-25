"""
documents.py — Document management REST endpoints.

Provides full CRUD + reprocess operations on uploaded documents.

Endpoints:
  GET  /documents                    — list all documents (newest first)
  GET  /documents/{document_id}      — detail view for one document
  DELETE /documents/{document_id}    — remove from MongoDB + ChromaDB + disk
  POST /documents/{document_id}/reprocess — re-run the ingestion pipeline

MongoDB documents are serialised with ObjectId → str and datetime → ISO string
so FastAPI can return them as clean JSON.
"""

from __future__ import annotations

import os
import logging
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.services.database import documents_collection, db
from app.services.vector_service import (
    delete_document_chunks,
    get_document_chunk_count,
)
from app.services.pdf_service import extract_pages
from app.services.chunk_service import chunk_pages
from app.services.embedding_service import generate_embedding
from app.services.vector_service import upsert_chunks
from app.config import UPLOAD_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


# ── Serialisation helper ──────────────────────────────────────────────────────

def _serialize(doc: dict) -> dict:
    """
    Convert a raw MongoDB document to a JSON-safe dict.

    - ObjectId  → str
    - datetime  → ISO-8601 string ending in Z
    - None      → kept as null
    """
    out: dict = {}
    for k, v in doc.items():
        if k == "_id":
            out["mongo_id"] = str(v)
        elif isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, datetime):
            # Ensure UTC marker so frontends parse it correctly
            if v.tzinfo is None:
                out[k] = v.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                out[k] = v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            out[k] = v
    return out


def _find_by_document_id(document_id: str) -> dict:
    """
    Look up a document by its string document_id field.
    Raises HTTP 404 if not found.
    """
    doc = documents_collection.find_one({"document_id": document_id})
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found.",
        )
    return doc


# ── GET /documents ────────────────────────────────────────────────────────────

@router.get("", summary="List all uploaded documents")
def list_documents(skip: int = 0, limit: int = 50):
    """
    Return all document records, newest first.

    Only returns documents created with the new pipeline (have a document_id).
    Legacy pre-Phase-2 records without a document_id are excluded.

    Query params:
      skip  — pagination offset (default 0)
      limit — max results (default 50, max 200)
    """
    limit = min(limit, 200)

    # Only return docs that have a proper document_id (Phase-2+ records)
    cursor = (
        documents_collection
        .find(
            {"document_id": {"$exists": True}},
            {"_id": 1, "document_id": 1, "filename": 1, "status": 1,
             "page_count": 1, "word_count": 1, "character_count": 1,
             "chunk_count": 1, "file_size_bytes": 1, "is_scanned": 1,
             "uploaded_at": 1, "processed_at": 1, "error": 1},
        )
        .sort("uploaded_at", -1)
        .skip(skip)
        .limit(limit)
    )

    docs = [_serialize(d) for d in cursor]

    total = documents_collection.count_documents(
        {"document_id": {"$exists": True}}
    )

    return {
        "total": total,
        "skip":  skip,
        "limit": limit,
        "documents": docs,
    }


# ── GET /documents/{document_id} ──────────────────────────────────────────────

@router.get("/{document_id}", summary="Get a single document's details")
def get_document(document_id: str):
    """
    Return full metadata for one document, including ChromaDB chunk count.
    """
    doc = _find_by_document_id(document_id)
    result = _serialize(doc)

    # Augment with live ChromaDB count so the frontend always sees truth
    result["chroma_chunk_count"] = get_document_chunk_count(document_id)

    # Determine whether the file still exists on disk
    filepath = doc.get("filepath", "")
    result["file_on_disk"] = bool(filepath and os.path.exists(filepath))

    return result


# ── DELETE /documents/{document_id} ───────────────────────────────────────────

@router.delete("/{document_id}", summary="Delete a document completely")
def delete_document(document_id: str):
    """
    Permanently remove a document:
      1. Delete all ChromaDB chunks
      2. Delete the PDF file from disk
      3. Remove the MongoDB record

    Returns a summary of what was deleted.
    """
    doc = _find_by_document_id(document_id)

    results: dict = {
        "document_id": document_id,
        "filename": doc.get("filename"),
        "chromadb_chunks_deleted": 0,
        "file_deleted": False,
        "mongo_record_deleted": False,
    }

    # 1. Remove vectors from ChromaDB
    try:
        deleted_chunks = delete_document_chunks(document_id)
        results["chromadb_chunks_deleted"] = deleted_chunks
    except Exception as exc:
        logger.warning(
            "ChromaDB deletion failed for %s (continuing): %s", document_id, exc
        )

    # 2. Delete file from disk
    filepath = doc.get("filepath", "")
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
            results["file_deleted"] = True
            logger.info("Deleted file: %s", filepath)
        except OSError as exc:
            logger.warning("Could not delete file %s: %s", filepath, exc)
    else:
        logger.info("File not found on disk (already deleted?): %s", filepath)

    # 3. Remove MongoDB record
    del_result = documents_collection.delete_one({"document_id": document_id})
    results["mongo_record_deleted"] = del_result.deleted_count == 1

    logger.info(
        "Deleted document '%s' (id=%s): %s",
        doc.get("filename"),
        document_id,
        results,
    )

    return {"status": "deleted", **results}


# ── POST /documents/{document_id}/reprocess ───────────────────────────────────

@router.post("/{document_id}/reprocess", summary="Re-run ingestion pipeline on a document")
def reprocess_document(document_id: str):
    """
    Re-run the full extraction → chunking → embedding → ChromaDB pipeline
    for an existing document.  Useful when:
      - The document previously failed processing
      - The chunking/embedding logic has been upgraded
      - The original run produced 0 chunks (e.g. scanned PDF)

    The PDF must still exist on disk.  The old ChromaDB chunks are replaced.
    """
    doc = _find_by_document_id(document_id)
    filepath = doc.get("filepath", "")

    if not filepath or not os.path.exists(filepath):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot reprocess '{doc.get('filename')}': "
                "the original PDF file is no longer on disk. "
                "Please delete this record and re-upload the document."
            ),
        )

    filename = doc.get("filename", "unknown.pdf")

    # ── Mark as processing ────────────────────────────────────────────────────
    documents_collection.update_one(
        {"document_id": document_id},
        {"$set": {"status": "processing", "error": None}},
    )

    try:
        # ── Remove old ChromaDB chunks ────────────────────────────────────────
        old_count = delete_document_chunks(document_id)
        logger.info(
            "Reprocess '%s': removed %d old chunks from ChromaDB", filename, old_count
        )

        # ── Re-run pipeline ───────────────────────────────────────────────────
        extraction = extract_pages(filepath)
        pages = extraction["pages"]

        chunks = chunk_pages(
            pages=pages,
            document_id=document_id,
            document_name=filename,
        )

        chunk_count_stored = 0
        if chunks:
            embeddings = [generate_embedding(c["text"]) for c in chunks]
            chunk_count_stored = upsert_chunks(chunks, embeddings)

        # ── Update MongoDB ────────────────────────────────────────────────────
        documents_collection.update_one(
            {"document_id": document_id},
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
            "Reprocessed '%s': %d pages, %d chunks",
            filename, extraction["page_count"], chunk_count_stored,
        )

        return {
            "document_id":    document_id,
            "filename":       filename,
            "status":         "processed",
            "page_count":     extraction["page_count"],
            "word_count":     extraction["word_count"],
            "chunk_count":    chunk_count_stored,
            "is_scanned":     extraction["is_scanned"],
            "old_chunks_removed": old_count,
        }

    except Exception as exc:
        error_msg = str(exc)
        logger.error("Reprocess failed for '%s': %s", filename, error_msg)
        documents_collection.update_one(
            {"document_id": document_id},
            {"$set": {"status": "failed", "error": error_msg}},
        )
        raise HTTPException(
            status_code=500,
            detail=f"Reprocessing failed: {error_msg}",
        )
