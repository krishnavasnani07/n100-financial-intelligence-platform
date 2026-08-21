from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.analytics.dna.dna_engine import FinancialDNAEngine
from src.api.database import clean_dict_nans

router = APIRouter(tags=["Financial DNA V2"])


class DNAMetrics(BaseModel):
    roe: Optional[float] = None
    roce: Optional[float] = None
    revenue_cagr: Optional[float] = None
    pat_cagr: Optional[float] = None
    debt_to_equity: Optional[float] = None
    interest_coverage: Optional[float] = None
    opm: Optional[float] = None


class ClusterAverage(BaseModel):
    roe: Optional[float] = None
    revenue_cagr: Optional[float] = None
    debt_to_equity: Optional[float] = None
    opm: Optional[float] = None


class QualityMetrics(BaseModel):
    silhouette_score: float
    davies_bouldin_index: float
    calinski_harabasz_index: float
    bootstrap_stability: float
    financial_interpretability: float


class ClusterQuality(BaseModel):
    financial_cluster_quality_score: float
    metrics: QualityMetrics


class CompanyDNAResponse(BaseModel):
    company_id: str
    year: str
    cluster_id: int
    archetype: str
    metrics: DNAMetrics
    cluster_average: ClusterAverage
    cluster_quality: ClusterQuality


@router.get("/analytics/dna/{ticker}", response_model=CompanyDNAResponse)
def get_company_financial_dna(
    ticker: str,
    year: str = Query("Mar 2024", description="Financial year to calculate DNA for"),
):
    """
    Fits multi-model clustering on the entire N100 universe for the selected year
    and returns the target company's cluster ID, archetype classification, metric comparison,
    and cluster quality metrics.
    """
    ticker = ticker.upper().strip()
    engine = FinancialDNAEngine()
    
    try:
        dna_data = engine.get_company_dna(ticker, year)
        return clean_dict_nans(dna_data)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clustering error: {e}")
