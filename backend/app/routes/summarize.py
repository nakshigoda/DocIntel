"""
summarize.py — Endpoints for document summarization and structured extraction.
"""

from __future__ import annotations

from fastapi import APIRouter
from app.services.summarization_service import summarize_document
from app.services.extraction_service import extract_structured_info

router = APIRouter(tags=["Intelligence"])

@router.post("/summarize/{document_id}", summary="Generate structured document summary")
def summarize(document_id: str):
    """
    Generate an executive summary, key points, clauses, risks, and action items for a document.
    """
    return summarize_document(document_id)

@router.post("/extract/{document_id}", summary="Extract structured information fields")
def extract(document_id: str):
    """
    Extract structured attributes (parties, dates, terms, clauses) from a document.
    """
    return extract_structured_info(document_id)
