import sqlite3
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.config.settings import DB_PATH

client = TestClient(app)


def get_a_valid_ticker_and_peer_group():
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT company_id, peer_group_name FROM peer_groups LIMIT 1"
        ).fetchone()
        if row:
            return row[0], row[1]
        return "TCS", "IT Services"
    except Exception:
        return "TCS", "IT Services"
    finally:
        conn.close()


def test_screener_endpoints():
    """Verify /api/v1/screener handles filtering, parameter validation, and errors."""
    # 1. Test basic filter
    res = client.get("/api/v1/screener?min_roe=15")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    for item in data:
        assert item["roe_pct"] >= 15

    # 2. Test multiple filters
    res = client.get("/api/v1/screener?min_roe=20&max_de=0.5&sector=IT")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    for item in data:
        assert item["roe_pct"] >= 20
        assert item["debt_to_equity"] <= 0.5
        assert "it" in item["sector"].lower()

    # 3. Test invalid float parameter value (reject "abc")
    res = client.get("/api/v1/screener?min_roe=abc")
    assert res.status_code == 400
    assert "min_roe" in res.json()["detail"]

    # 4. Test negative max_de validation
    res = client.get("/api/v1/screener?max_de=-1")
    assert res.status_code == 400
    assert "max_de" in res.json()["detail"]

    # 5. Test invalid sector
    res = client.get("/api/v1/screener?sector=invalid_sector_name")
    assert res.status_code == 400
    assert "invalid_sector_name" in res.json()["detail"]


def test_sectors_endpoints():
    """Verify /api/v1/sectors and /api/v1/sectors/{sector}/companies."""
    # 1. Test sectors overview
    res = client.get("/api/v1/sectors")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 11
    first_sec = data[0]
    assert "sector" in first_sec
    assert "company_count" in first_sec
    assert "median_roe" in first_sec
    assert "median_pe" in first_sec
    assert "median_de" in first_sec

    # 2. Test valid sector companies
    res = client.get("/api/v1/sectors/IT Services/companies")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if data:
        assert data[0]["sector"] == "IT Services"

    # 3. Test invalid sector companies returns 404
    res = client.get("/api/v1/sectors/invalid_sec/companies")
    assert res.status_code == 404


def test_peers_endpoints():
    """Verify /api/v1/peers/{group_name} and comparison routes."""
    ticker, group_name = get_a_valid_ticker_and_peer_group()

    # 1. Test peer group details
    res = client.get(f"/api/v1/peers/{group_name}")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first_item = data[0]
    assert "company_id" in first_item
    assert "is_benchmark" in first_item
    assert "metrics" in first_item
    assert "percentiles" in first_item

    # 2. Test invalid peer group returns 404
    res = client.get("/api/v1/peers/non_existent_group")
    assert res.status_code == 404

    # 3. Test peer comparison
    res = client.get(f"/api/v1/companies/{ticker}/peers/compare")
    assert res.status_code == 200
    data = res.json()
    assert "axes" in data
    assert "company" in data
    assert "benchmark" in data
    assert data["company"]["ticker"] == ticker
    assert len(data["axes"]) == 8

    # 4. Test invalid company comparison returns 404
    res = client.get("/api/v1/companies/INVALIDCOMP/peers/compare")
    assert res.status_code == 404


def test_valuation_history_endpoint():
    """Verify /api/v1/market-cap/{ticker}."""
    ticker, _ = get_a_valid_ticker_and_peer_group()

    # 1. Test valid ticker
    res = client.get(f"/api/v1/market-cap/{ticker}")
    assert res.status_code == 200
    data = res.json()
    assert data["ticker"] == ticker
    assert isinstance(data["history"], list)
    assert len(data["history"]) > 0
    first_hist = data["history"][0]
    assert "year" in first_hist
    assert "pe" in first_hist
    assert "pb" in first_hist
    assert "ev_ebitda" in first_hist
    assert "dividend_yield" in first_hist

    # 2. Test invalid ticker returns 404
    res = client.get("/api/v1/market-cap/INVALIDCOMP")
    assert res.status_code == 404


def test_portfolio_stats_endpoint():
    """Verify /api/v1/portfolio/stats."""
    res = client.get("/api/v1/portfolio/stats")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 10
    first_stat = data[0]
    assert "kpi" in first_stat
    assert "p10" in first_stat
    assert "p25" in first_stat
    assert "p50" in first_stat
    assert "p75" in first_stat
    assert "p90" in first_stat


def test_company_documents_endpoint():
    """Verify /api/v1/companies/{ticker}/documents."""
    ticker, _ = get_a_valid_ticker_and_peer_group()

    # 1. Test valid ticker
    res = client.get(f"/api/v1/companies/{ticker}/documents")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    # Even if empty (e.g. no documents loaded in DB), it should be a list
    if data:
        first_doc = data[0]
        assert "company_id" in first_doc
        assert "annual_report" in first_doc

    # 2. Test invalid ticker returns 404
    res = client.get("/api/v1/companies/INVALIDCOMP/documents")
    assert res.status_code == 404
