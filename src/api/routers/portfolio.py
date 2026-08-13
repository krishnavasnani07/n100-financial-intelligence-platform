from fastapi import APIRouter

router = APIRouter(tags=["Portfolio"])


@router.get("/portfolio/placeholder")
def get_portfolio_placeholder():
    """Placeholder endpoint for Portfolio router."""
    return {
        "message": "Portfolio endpoint is under construction. Coming soon in Day 40!"
    }
