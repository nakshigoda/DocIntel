"""
vector_service.py — ChromaDB persistence layer for DocIntel AI.

Replaces the FAISS-based faiss_service.py for all new uploads.
faiss_service.py is retained (but unused for new data) until this
service has been fully verified, then it will be removed.

ChromaDB collection: "document_chunks"
Each record stores:
  - id:       chunk_id  (unique string, encodes doc/page/chunk position)
  - embedding: 384-dim float list (sentence_transformers)
  - document: chunk text
  - metadata: document_id, document_name, page_number, chunk_index
"""

from __future__ import annotations

import logging
from typing import Optional
import chromadb
from app.config import VECTOR_DB_DIR

logger = logging.getLogger(__name__)

# Module-level singletons — one client and one collection for the process lifetime
# Use Any-typed vars to avoid runtime evaluation of chromadb type annotations
_client = None   # chromadb.ClientAPI
_collection = None  # chromadb.Collection
_COLLECTION_NAME = "document_chunks"


def _get_collection() -> chromadb.Collection:
    """
    Return the ChromaDB collection, initialising the persistent client on
    first call.  cosine similarity is used so scores map naturally to [0, 1].
    """
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=VECTOR_DB_DIR)
        _collection = _client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB collection '%s' ready at '%s' (%d existing chunks)",
            _COLLECTION_NAME,
            VECTOR_DB_DIR,
            _collection.count(),
        )
    return _collection


# ── Write ─────────────────────────────────────────────────────────────────────

def upsert_chunks(
    chunks: list[dict],
    embeddings: list[list[float]],
) -> int:
    """
    Upsert a batch of chunks into ChromaDB.

    Args:
        chunks:     list of ChunkResult dicts from chunk_service.chunk_pages()
        embeddings: parallel list of embedding vectors

    Returns:
        Number of chunks upserted.
    """
    if not chunks:
        logger.warning("upsert_chunks called with empty chunk list — nothing stored")
        return 0

    collection = _get_collection()

    ids        = [c["chunk_id"] for c in chunks]
    documents  = [c["text"] for c in chunks]
    metadatas  = [
        {
            "document_id":   c["document_id"],
            "document_name": c["document_name"],
            "page_number":   c["page_number"],
            "chunk_index":   c["chunk_index"],
        }
        for c in chunks
    ]

    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    logger.info("Upserted %d chunks into ChromaDB", len(chunks))
    return len(chunks)


# ── Read ──────────────────────────────────────────────────────────────────────

def search_chunks(
    query_embedding: list[float],
    k: int = 5,
    document_id: Optional[str] = None,
) -> list[dict]:
    """
    Semantic nearest-neighbour search in ChromaDB.

    Args:
        query_embedding: vector for the user query
        k:               max results to return
        document_id:     if provided (and not "all"), filter to one document

    Returns:
        list of hit dicts, each containing:
            chunk_id, text, document_id, document_name, page_number, score
        Sorted by descending similarity score.
    """
    collection = _get_collection()
    total = collection.count()

    if total == 0:
        logger.info("ChromaDB is empty — returning no results")
        return []

    # Build optional metadata filter
    where: Optional[dict] = None
    if document_id and document_id != "all":
        where = {"document_id": {"$eq": document_id}}

    actual_k = min(k, total)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=actual_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    hits: list[dict] = []
    if results["ids"] and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            # ChromaDB cosine distance: 0 = identical, 1 = orthogonal, 2 = opposite
            distance = results["distances"][0][i]
            score = round(max(0.0, 1.0 - distance), 4)  # convert to similarity
            meta = results["metadatas"][0][i]
            hits.append(
                {
                    "chunk_id":      chunk_id,
                    "text":          results["documents"][0][i],
                    "document_id":   meta["document_id"],
                    "document_name": meta["document_name"],
                    "page_number":   meta["page_number"],
                    "score":         score,
                }
            )

    logger.info(
        "ChromaDB search returned %d results (k=%d, filter_doc=%s)",
        len(hits),
        k,
        document_id,
    )
    return hits


# ── Delete ────────────────────────────────────────────────────────────────────

def delete_document_chunks(document_id: str) -> int:
    """
    Remove all chunks for a given document_id from ChromaDB.

    Returns:
        Number of chunks deleted.
    """
    collection = _get_collection()

    existing = collection.get(
        where={"document_id": {"$eq": document_id}},
        include=[],
    )
    ids = existing["ids"]

    if ids:
        collection.delete(ids=ids)
        logger.info("Deleted %d chunks for document %s", len(ids), document_id)
    else:
        logger.info("No chunks found in ChromaDB for document %s", document_id)

    return len(ids)


def get_document_chunk_count(document_id: str) -> int:
    """Return how many chunks are stored for a document."""
    collection = _get_collection()
    result = collection.get(
        where={"document_id": {"$eq": document_id}},
        include=[],
    )
    return len(result["ids"])


def total_chunk_count() -> int:
    """Return total number of chunks stored in ChromaDB."""
    return _get_collection().count()
