from __future__ import annotations

import threading
import logging
from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL, EMBEDDING_DIM

logger = logging.getLogger(__name__)

# Module-level singleton — thread-safe double-checked locking
_model: SentenceTransformer | None = None
_lock = threading.Lock()


def _get_model() -> SentenceTransformer:
    """Load the SentenceTransformer model once and cache it."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
                _model = SentenceTransformer(EMBEDDING_MODEL)
                logger.info(f"Embedding model loaded (dim={EMBEDDING_DIM})")
    return _model


def generate_embedding(text: str) -> list[float]:
    """
    Generate a {EMBEDDING_DIM}-dimensional embedding for the given text.
    Uses sentence_transformers locally — no API key required.
    """
    model = _get_model()
    return model.encode(text, show_progress_bar=False).tolist()