from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_get_sectors():
    """Verify /api/v1/sectors returns exactly 11 standardized sectors and their stats."""
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 11

    # Verify required keys in each sector statistics representation
    for sector_stat in data:
        assert "sector" in sector_stat
        assert "company_count" in sector_stat
        assert "median_roe" in sector_stat
        assert "median_pe" in sector_stat
        assert "median_de" in sector_stat
        assert sector_stat["company_count"] >= 0


def test_get_sector_companies_valid():
    """Verify GET /api/v1/sectors/IT/companies returns companies in the IT sector."""
    response = client.get("/api/v1/sectors/IT/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for company in data:
        assert company["sector"] == "IT Services"


def test_get_sector_companies_invalid():
    """Verify GET /api/v1/sectors/INVALID/companies returns HTTP 404."""
    response = client.get("/api/v1/sectors/INVALID/companies")
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"].lower()
