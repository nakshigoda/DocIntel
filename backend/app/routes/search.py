"""
search.py — Semantic search endpoint (ChromaDB-backed).
"""

import logging
from fastapi import APIRouter
from app.services.embedding_service import generate_embedding
from app.services.vector_service import search_chunks

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Search"])


@router.get("/search", summary="Semantic search across uploaded documents")
def search_docs(query: str, document_id: str = "all", k: int = 5):
    """
    Embed the query and return the top-k most relevant chunks.

    Returns each hit with document name, page number, relevance score,
    and a text snippet — ready to display as search results.
    """
    if not query.strip():
        return {"query": query, "results": [], "total": 0}

    query_embedding = generate_embedding(query)
    filter_doc = None if document_id == "all" else document_id

    results = search_chunks(
        query_embedding=query_embedding,
        k=min(k, 20),          # cap at 20 to avoid unreasonable requests
        document_id=filter_doc,
    )

    logger.info(
        "Search: query='%s', returned=%d results, filter_doc=%s",
        query[:80],
        len(results),
        document_id,
    )

    return {
        "query":   query,
        "results": [
            {
                "document_id":   r["document_id"],
                "document_name": r["document_name"],
                "page_number":   r["page_number"],
                "snippet":       r["text"][:400],
                "score":         r["score"],
            }
            for r in results
        ],
        "total": len(results),
    }