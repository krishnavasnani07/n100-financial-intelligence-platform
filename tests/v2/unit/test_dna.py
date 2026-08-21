from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.v2.unit.test_repositories import test_db_path
from src.analytics.dna.dna_engine import FinancialDNAEngine
from src.api.main import app


def test_prepare_features(test_db_path: Path):
    engine = FinancialDNAEngine(db_path=test_db_path)
    df = engine.prepare_features("Mar 2024")
    
    assert len(df) == 5  # TCS, INFY, RELIANCE, HDFCBANK, LT
    assert "TCS" in df.index
    assert "INFY" in df.index
    assert list(df.columns) == ["roe", "roce", "revenue_cagr", "pat_cagr", "debt_to_equity", "interest_coverage", "opm"]
    
    # Check imputation works (e.g. interest_coverage in mock data)
    assert not df.isnull().any().any()


def test_fit_clusters(test_db_path: Path):
    engine = FinancialDNAEngine(db_path=test_db_path)
    df = engine.prepare_features("Mar 2024")
    
    # Fit with 4 clusters
    fit_res = engine.fit_clusters(df, n_clusters=4)
    
    assert "kmeans_labels" in fit_res
    assert len(fit_res["kmeans_labels"]) == 5
    assert "metrics" in fit_res
    assert fit_res["financial_cluster_quality_score"] > 0
    assert "archetype_map" in fit_res
    assert len(fit_res["archetype_map"]) == 4


def test_get_company_dna(test_db_path: Path):
    engine = FinancialDNAEngine(db_path=test_db_path)
    
    dna = engine.get_company_dna("TCS", "Mar 2024")
    assert dna["company_id"] == "TCS"
    assert dna["year"] == "Mar 2024"
    assert dna["cluster_id"] in [0, 1, 2, 3]
    assert "archetype" in dna
    assert dna["metrics"]["roe"] == 48.2
    assert dna["cluster_average"]["roe"] is not None
    assert dna["cluster_quality"]["financial_cluster_quality_score"] > 0


def test_dna_api_endpoint():
    client = TestClient(app)
    
    # Query DNA endpoint on the real database for TCS
    response = client.get("/api/v2/analytics/dna/TCS?year=Mar 2024")
    assert response.status_code == 200
    
    data = response.json()
    assert data["company_id"] == "TCS"
    assert data["year"] == "Mar 2024"
    assert "archetype" in data
    assert "metrics" in data
    assert "cluster_average" in data
    assert "cluster_quality" in data
    
    # Query invalid company ticker
    response_invalid = client.get("/api/v2/analytics/dna/INVALIDTICKER")
    assert response_invalid.status_code == 404
