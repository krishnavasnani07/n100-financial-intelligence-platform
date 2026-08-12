import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from src.portfolio.portfolio_engine import calculate_portfolio_metrics
from src.forecasting.forecasting_engine import generate_company_forecasts
from src.utils.ai_engine import get_company_insights_data
from src.api.main import app


def test_api_endpoints():
    """Verify FastAPI endpoints return success code and expected JSON structures."""
    client = TestClient(app)

    # 1. Test root endpoint
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "status" in res_root.json()
    assert res_root.json()["status"] == "healthy"

    # 2. Test peer comparison endpoint
    res_peer = client.get("/api/peercomparison")
    assert res_peer.status_code == 200
    data_peer = res_peer.json()
    assert len(data_peer) > 0
    assert "Company" in data_peer[0]
    assert "Peer Rank" in data_peer[0]

    # 3. Test top performers endpoint
    res_top = client.get("/api/topperformers")
    assert res_top.status_code == 200
    data_top = res_top.json()
    assert len(data_top) > 0
    assert "Composite Score" in data_top[0]

    # 4. Test company ratios endpoint
    test_company = data_peer[0]["Company"]
    res_company = client.get(f"/api/company/{test_company}")
    assert res_company.status_code == 200
    data_comp = res_company.json()
    assert data_comp["company_id"] == test_company

    # 5. Test sector endpoint
    test_sector = data_peer[0]["Sector"]
    res_sector = client.get(f"/api/sector/{test_sector}")
    assert res_sector.status_code == 200
    data_sec = res_sector.json()
    assert data_sec["sector"] == test_sector
    assert "companies" in data_sec
    assert len(data_sec["companies"]) > 0


def test_portfolio_metrics_builder():
    """Test portfolio analytics metric calculations with a mock allocation."""
    allocations = {"TCS": 0.6, "INFY": 0.4}
    metrics = calculate_portfolio_metrics(allocations)

    assert "expected_return" in metrics
    assert "volatility" in metrics
    assert "sharpe_ratio" in metrics
    assert "beta" in metrics
    assert "diversification_score" in metrics

    # Weights should sum to 100% and diversification score for 2 assets should be positive
    assert metrics["diversification_score"] > 0.0
    assert (
        metrics["diversification_score"] <= 52.0
    )  # (1 - (0.6^2 + 0.4^2)) * 100 = 48.0


def test_forecasting_engine_trend():
    """Verify forecasting engine is generating correct projections and growth rate trend lines."""
    # Run forecasting on a company that exists in our db (e.g. TCS)
    res = generate_company_forecasts("TCS")
    assert res["success"] is True
    assert "historical" in res
    assert "forecasts" in res
    assert len(res["forecasts"]) == 3
    assert "revenue_trend_growth_rate" in res
    assert "eps_trend_growth_rate" in res


def test_ai_insights_summary():
    """Verify AI Engine compiles text insights and recommendations with required keys."""
    res = get_company_insights_data("TCS")
    assert res["success"] is True
    assert "summary" in res
    assert "recommendation" in res
    assert "matched_screeners" in res
    assert "TCS" in res["summary"]
