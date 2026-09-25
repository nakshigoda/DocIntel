from fastapi import APIRouter
from app.utils.text_chunker import chunk_text
from app.services.embedding_service import generate_embedding
from app.services.faiss_service import add_embeddings

router = APIRouter()

@router.post("/ingest")
def ingest_document(text: str):

    chunks = chunk_text(text)

    embeddings = [generate_embedding(c) for c in chunks]

    add_embeddings(embeddings, chunks)

    return {
        "status": "success",
        "chunks": len(chunks)
    }