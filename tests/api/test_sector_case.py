from fastapi.testclient import TestClient

from src.api.main import app
from src.api.routers.sectors import normalize_sector_name

client = TestClient(app)


def test_normalize_sector_name():
    # Test valid mappings
    assert normalize_sector_name("it") == "IT Services"
    assert normalize_sector_name("IT SERVICES") == "IT Services"
    assert normalize_sector_name("Information Technology") == "IT Services"
    assert normalize_sector_name("banking") == "Banking"
    assert normalize_sector_name("Financials") == "Banking"
    assert normalize_sector_name("  Utilities  ") == "Utilities"

    # Test invalid mapping
    assert normalize_sector_name("NonExistentSector") is None


def test_sector_companies_exact_case():
    response = client.get("/api/v1/sectors/Utilities/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for company in data:
        assert company["sector"] == "Utilities"


def test_sector_companies_lowercase():
    response = client.get("/api/v1/sectors/utilities/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for company in data:
        assert company["sector"] == "Utilities"


def test_sector_companies_uppercase_mapping():
    response = client.get("/api/v1/sectors/IT/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for company in data:
        assert company["sector"] == "IT Services"


def test_sector_companies_with_whitespace():
    response = client.get("/api/v1/sectors/  banking  /companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for company in data:
        assert company["sector"] == "Banking"


def test_sector_companies_invalid():
    response = client.get("/api/v1/sectors/NotASector/companies")
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]
