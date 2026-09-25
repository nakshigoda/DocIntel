"""
main.py — DocIntel AI FastAPI application entry point.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Routes ────────────────────────────────────────────────────────────────────
from app.routes.upload import router as upload_router
from app.routes.test_db import router as db_router
from app.routes.chunk_test import router as chunk_router
from app.routes.test_embedding import router as embedding_router
from app.routes.document import router as document_router          # legacy /ingest
from app.routes.documents import router as documents_router        # Phase-3 management
from app.routes.search import router as search_router
from app.routes.chat import router as chat_router
from app.routes.summarize import router as summarize_router
from app.routes.compare import router as compare_router

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="DocIntel AI",
    version="2.0.0",
    description=(
        "Enterprise Document Intelligence Platform — "
        "RAG, semantic search, and document insights powered by Groq + ChromaDB."
    ),
)

# CORS — must be registered before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ──────────────────────────────────────────────────────────
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(search_router)
app.include_router(documents_router)   # Phase-3: /documents management
app.include_router(summarize_router)   # Phase-4: /summarize and /extract
app.include_router(compare_router)     # Phase-5: /compare
app.include_router(document_router)    # legacy: /ingest debug endpoint
# Debug / test routes (kept for development convenience)
app.include_router(db_router)
app.include_router(chunk_router)
app.include_router(embedding_router)


# ── Root & Health ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"], summary="Root")
def root():
    return {
        "project": "DocIntel AI",
        "version": "2.0.0",
        "status":  "running",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Health"], summary="Health check")
def health():
    """Simple liveness check — returns 200 if the service is up."""
    return {"status": "ok"}