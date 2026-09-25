from fastapi import APIRouter
from app.services.embedding_service import generate_embedding

router = APIRouter()

@router.get("/test-embedding")
def test_embedding():
    try:
        embedding = generate_embedding("Hello World")
        return {
            "status": "ok",
            "dim": len(embedding),
            "sample": embedding[:5]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }