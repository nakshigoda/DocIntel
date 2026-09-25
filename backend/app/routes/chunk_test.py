from fastapi import APIRouter

from app.services.chunk_service import (
    chunk_text
)

router = APIRouter()


@router.post("/test-chunk")
def test_chunk():

    sample_text = (
        "Hello World " * 500
    )

    chunks = chunk_text(
        sample_text
    )

    return {

        "total_chunks":
            len(chunks),

        "first_chunk":
            chunks[0][:200]
    }