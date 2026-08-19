from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_screener_min_roe():
    """Verify min_roe=15 returns only companies with ROE >= 15."""
    response = client.get("/api/v1/screener?min_roe=15")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for company in data:
        assert company["roe_pct"] >= 15.0


def test_screener_invalid_param():
    """Verify invalid parameter returns HTTP 400."""
    response = client.get("/api/v1/screener?min_roe=abc")
    assert response.status_code == 400
    assert "min_roe" in response.json()["detail"].lower()


def test_screener_negative_de():
    """Verify negative max_de returns HTTP 400."""
    response = client.get("/api/v1/screener?max_de=-1.0")
    assert response.status_code == 400
    assert "max_de" in response.json()["detail"].lower()


def test_screener_no_filters():
    """Verify GET /api/v1/screener returns all companies when no filters are applied."""
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 92


def test_screener_sector_filter():
    """Verify sector filter IT maps to IT Services and returns correct results."""
    response = client.get("/api/v1/screener?sector=IT")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for company in data:
        assert company["sector"] == "IT Services"


def test_screener_max_de_filter():
    """Verify max_de=1 returns only companies with debt_to_equity <= 1, skipping Financials."""
    response = client.get("/api/v1/screener?max_de=1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    for company in data:
        if company["sector"].lower() in ["banking", "financials"]:
            continue
        assert company["debt_to_equity"] <= 1.0


def test_screener_multi_filters():
    """Verify combining multiple filters returns correct intersection of criteria."""
    response = client.get("/api/v1/screener?min_roe=15&max_pe=30")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for company in data:
        assert company["roe_pct"] >= 15.0
        if "pe" in company and company["pe"] is not None:
            assert company["pe"] <= 30.0
