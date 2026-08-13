from fastapi import APIRouter

router = APIRouter(tags=["Documents"])


@router.get("/documents/placeholder")
def get_documents_placeholder():
    """Placeholder endpoint for Documents router."""
    return {
        "message": "Documents endpoint is under construction. Coming soon in Day 40!"
    }
