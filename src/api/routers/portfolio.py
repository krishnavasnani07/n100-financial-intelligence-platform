from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict
from src.portfolio.portfolio_engine import calculate_portfolio_metrics

router = APIRouter(tags=["Portfolio"])


class PortfolioAnalysisRequest(BaseModel):
    allocations: Dict[str, float] = Field(
        ...,
        description="Dictionary mapping company ticker (keys) to their weight/allocation (values)",
        json_schema_extra={"example": {"TCS": 0.4, "INFY": 0.4, "ABB": 0.2}},
    )
    risk_free_rate: float = Field(
        7.0,
        description="Risk-free rate in percentage points",
        json_schema_extra={"example": 7.0},
    )


@router.post("/portfolio/analyze")
def analyze_portfolio(req: PortfolioAnalysisRequest):
    """
    Computes portfolio metrics: Expected Return, Volatility, Sharpe Ratio, Beta, and Diversification.
    """
    if not req.allocations:
        raise HTTPException(
            status_code=400,
            detail="Allocations dictionary cannot be empty.",
        )
    for ticker, weight in req.allocations.items():
        if weight < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Allocation for {ticker} cannot be negative.",
            )
    try:
        metrics = calculate_portfolio_metrics(
            allocations=req.allocations, risk_free_rate=req.risk_free_rate
        )
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating portfolio metrics: {e}",
        )
