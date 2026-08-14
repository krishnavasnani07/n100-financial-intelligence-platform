from fastapi.testclient import TestClient
from src.api.main import app
import pytest

client = TestClient(app)


def test_analyze_portfolio_success():
    """Verify that POST /api/v1/portfolio/analyze succeeds with valid data."""
    payload = {"allocations": {"TCS": 0.5, "INFY": 0.5}, "risk_free_rate": 7.0}
    response = client.post("/api/v1/portfolio/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "expected_return" in data
    assert "volatility" in data
    assert "sharpe_ratio" in data
    assert "beta" in data
    assert "diversification_score" in data


def test_analyze_portfolio_invalid():
    """Verify that POST /api/v1/portfolio/analyze handles bad requests."""
    # Empty allocations
    payload = {"allocations": {}, "risk_free_rate": 7.0}
    response = client.post("/api/v1/portfolio/analyze", json=payload)
    assert response.status_code == 400

    # Negative allocation
    payload = {"allocations": {"TCS": -0.5}, "risk_free_rate": 7.0}
    response = client.post("/api/v1/portfolio/analyze", json=payload)
    assert response.status_code == 400


def test_get_portfolio_summary_document():
    """Verify download of portfolio-summary report."""
    response = client.get("/api/v1/documents/portfolio-summary")
    # If the file exists, it should be 200, otherwise 404
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert response.headers["content-type"] == "application/pdf"


def test_get_peer_report_document():
    """Verify download of peer-report."""
    response = client.get("/api/v1/documents/peer-report")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert response.headers["content-type"] == "application/pdf"


def test_get_sector_report_document():
    """Verify download of sector-report with valid/invalid names."""
    response = client.get("/api/v1/documents/sector-report/IT")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        assert response.headers["content-type"] == "application/pdf"

    # Invalid sector name
    response = client.get("/api/v1/documents/sector-report/NONEXISTENTSECTOR")
    assert response.status_code == 404
