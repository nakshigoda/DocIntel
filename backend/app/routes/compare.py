"""
compare.py — Endpoint for comparing two documents.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.comparison_service import compare_documents

router = APIRouter(tags=["Intelligence"])

class CompareRequest(BaseModel):
    document_id_a: str
    document_id_b: str

@router.post("/compare", summary="Compare two documents")
def compare(req: CompareRequest):
    """
    Compare two documents to analyze additions, removals, changed clauses, and risk impact.
    """
    if req.document_id_a == req.document_id_b:
        raise HTTPException(
            status_code=400,
            detail="document_id_a and document_id_b must be different."
        )
    return compare_documents(req.document_id_a, req.document_id_b)
