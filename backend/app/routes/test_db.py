from fastapi import APIRouter
from app.services.database import documents_collection

router = APIRouter()

@router.get("/test-db")
def test_db():

    documents_collection.insert_one(
        {
            "message": "MongoDB Connected"
        }
    )

    return {
        "status": "success"
    }