from fastapi.testclient import TestClient
from src.api.main import app


def test_health_endpoint():
    client = TestClient(app)
    res = client.get("/api/v1/health")
    assert res.status_code == 200

    data = res.json()
    assert data["status"] == "ok"
    assert "db_row_counts" in data
    assert "uptime_seconds" in data
    assert data["version"] == "1.0.0"

    # Ensure row count for companies table is in the response and is 92
    assert "companies" in data["db_row_counts"]
    assert data["db_row_counts"]["companies"] == 92


def test_cors_headers():
    client = TestClient(app)
    res = client.get("/api/v1/health", headers={"Origin": "http://example.com"})
    assert res.status_code == 200
    assert "access-control-allow-origin" in res.headers
    assert res.headers["access-control-allow-origin"] == "http://example.com"


def test_placeholders():
    client = TestClient(app)

    res_port = client.get("/api/v1/portfolio/placeholder")
    assert res_port.status_code == 200
    assert "under construction" in res_port.json()["message"]

    res_docs = client.get("/api/v1/documents/placeholder")
    assert res_docs.status_code == 200
    assert "under construction" in res_docs.json()["message"]
