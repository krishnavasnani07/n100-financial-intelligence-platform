
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.config.settings import DB_PATH, OUTPUT_DIR
from src.portfolio.portfolio_engine import calculate_portfolio_metrics
from src.screener.ranking import calculate_rankings

router = APIRouter(tags=["Portfolio"])


class PortfolioAnalysisRequest(BaseModel):
    allocations: dict[str, float] = Field(
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


@router.get("/portfolio/stats")
def get_portfolio_stats():
    """
    Returns a percentile breakdown (P10, P25, P50, P75, P90) of 10 core KPIs across all 92 companies.
    """
    try:
        csv_path = OUTPUT_DIR / "csv" / "rankings.csv"
        if not csv_path.exists():
            df = calculate_rankings(DB_PATH)
        else:
            df = pd.read_csv(csv_path)

        kpis = [
            "return_on_equity_pct",
            "return_on_capital_employed_pct",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "debt_to_equity",
            "interest_coverage",
            "free_cash_flow_cr",
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "composite_quality_score",
        ]

        percentiles = [10, 25, 50, 75, 90]
        results = []

        for kpi in kpis:
            series = df[kpi].dropna()
            if not series.empty:
                p_vals = np.percentile(series, percentiles)
                p10, p25, p50, p75, p90 = p_vals
            else:
                p10 = p25 = p50 = p75 = p90 = 0.0

            results.append(
                {
                    "kpi": kpi,
                    "p10": round(float(p10), 2),
                    "p25": round(float(p25), 2),
                    "p50": round(float(p50), 2),
                    "p75": round(float(p75), 2),
                    "p90": round(float(p90), 2),
                }
            )

        # Save to output/portfolio_stats.csv if not existing
        csv_out_path = OUTPUT_DIR / "portfolio_stats.csv"
        if not csv_out_path.exists():
            csv_out_path.parent.mkdir(parents=True, exist_ok=True)
            stats_df = pd.DataFrame(results)
            stats_df.to_csv(csv_out_path, index=False)

        return results
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error compiling portfolio stats: {e}"
        )


@router.get("/portfolio/placeholder")
def get_portfolio_placeholder():
    """Placeholder endpoint for scaffold tests."""
    return {"message": "under construction"}
