"""
chat.py — RAG question-answering endpoint.

Uses ChromaDB for retrieval and Groq (llama-3.1-8b-instant) for generation.
GET /chat is kept for backward compatibility with the existing frontend.
"""

import logging
from fastapi import APIRouter
from app.services.embedding_service import generate_embedding
from app.services.vector_service import search_chunks
from app.services.llm_service import generate_answer

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Chat"])


@router.get("/chat", summary="Ask a question about uploaded documents (RAG)")
def chat(query: str, document_id: str = "all"):
    """
    Retrieval-Augmented Generation endpoint.

    - Embeds the query
    - Retrieves top-5 relevant chunks from ChromaDB
    - Sends context + question to Groq LLM
    - Returns grounded answer with source citations (document, page)

    Set document_id to a specific ID to query a single document,
    or leave as "all" to search across all uploaded documents.
    """
    if not query.strip():
        return {"query": query, "answer": "Please provide a question.", "sources": []}

    # ── Retrieve relevant chunks ──────────────────────────────────────────────
    query_embedding = generate_embedding(query)

    filter_doc = None if document_id == "all" else document_id
    results = search_chunks(query_embedding=query_embedding, k=5, document_id=filter_doc)

    if not results:
        return {
            "query":  query,
            "answer": (
                "No relevant information was found in the uploaded documents. "
                "Please upload a document first, or try rephrasing your question."
            ),
            "sources": [],
        }

    # ── Build context for LLM ─────────────────────────────────────────────────
    context_parts = [
        f"[Source: {r['document_name']}, Page {r['page_number']}]\n{r['text']}"
        for r in results
    ]
    context = "\n\n---\n\n".join(context_parts)

    logger.info(
        "RAG: query='%s', retrieved=%d chunks, filter_doc=%s",
        query[:80],
        len(results),
        document_id,
    )

    # ── Generate grounded answer ──────────────────────────────────────────────
    answer = generate_answer(context=context, query=query)

    return {
        "query":  query,
        "answer": answer,
        "sources": [
            {
                "document_id":   r["document_id"],
                "document_name": r["document_name"],
                "page_number":   r["page_number"],
                "snippet":       r["text"][:300],
                "score":         r["score"],
            }
            for r in results
        ],
    }