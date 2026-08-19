from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

# The 10 core expected tables in the database schema
EXPECTED_TABLES = {
    "companies",
    "sectors",
    "analysis",
    "prosandcons",
    "profitandloss",
    "balancesheet",
    "cashflow",
    "documents",
    "stock_prices",
    "financial_ratios",
}


def test_health_status_code():
    """Verify GET /api/v1/health returns HTTP 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_status_ok():
    """Verify GET /api/v1/health returns status='ok'."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_database_row_counts():
    """Verify GET /api/v1/health contains all 10 expected tables in db_row_counts."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert "db_row_counts" in data

    db_counts = data["db_row_counts"]
    for table in EXPECTED_TABLES:
        assert (
            table in db_counts
        ), f"Expected table '{table}' not found in db_row_counts"
        assert db_counts[table] >= 0, f"Table '{table}' has negative row count"

    # Specific sanity check
    assert db_counts["companies"] == 92
