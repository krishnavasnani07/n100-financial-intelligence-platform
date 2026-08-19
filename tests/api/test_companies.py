from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_get_companies_default():
    """Verify that GET /api/v1/companies returns 200 and all 92 companies."""
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "companies" in data
    assert data["count"] == 92
    assert len(data["companies"]) == 92
    first_company = data["companies"][0]
    assert "id" in first_company
    assert "ticker" in first_company
    assert "company_name" in first_company
    assert "sector" in first_company
    assert "broad_sector" in first_company
    assert "sub_sector" in first_company
    assert "market_cap_category" in first_company
    assert "roe" in first_company
    assert "roce" in first_company


def test_get_companies_filters():
    """Verify sector, market cap, and search query filters on GET /api/v1/companies."""
    # Sector filter
    response = client.get("/api/v1/companies?sector=IT")
    assert response.status_code == 200
    data = response.json()
    for company in data["companies"]:
        assert (
            company["sector"].lower() == "it" or company["broad_sector"].lower() == "it"
        )

    # Market Cap filter
    response = client.get("/api/v1/companies?market_cap_category=Large Cap")
    assert response.status_code == 200
    data = response.json()
    for company in data["companies"]:
        assert company["market_cap_category"].lower() == "large cap"

    # Search filter
    response = client.get("/api/v1/companies?search=tata")
    assert response.status_code == 200
    data = response.json()
    for company in data["companies"]:
        assert (
            "tata" in company["company_name"].lower()
            or "tata" in company["ticker"].lower()
        )


def test_get_company_profile():
    """Verify GET /api/v1/companies/{ticker} for valid and invalid tickers."""
    # Valid ticker
    response = client.get("/api/v1/companies/TCS")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "TCS"
    assert "company_name" in data
    assert "about_company" in data
    assert "website" in data
    assert "latest_year" in data
    assert "kpis" in data
    assert isinstance(data["pros"], list)
    assert isinstance(data["cons"], list)

    # Invalid ticker
    response = client.get("/api/v1/companies/INVALIDTICKER")
    assert response.status_code == 404
    assert "detail" in response.json()

    response2 = client.get("/api/v1/companies/INVALID")
    assert response2.status_code == 404
    assert "detail" in response2.json()


def test_get_company_pl():
    """Verify GET /api/v1/companies/{ticker}/pl historical endpoint and filters."""
    # Valid pl
    response = client.get("/api/v1/companies/TCS/pl")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "sales" in data[0]
    assert "net_profit" in data[0]

    # Year filter
    response = client.get("/api/v1/companies/TCS/pl?from_year=2020&to_year=2024")
    assert response.status_code == 200
    for record in response.json():
        # extract year suffix
        year_str = str(record["year"])
        digits = "".join(c for c in year_str if c.isdigit())
        if len(digits) >= 4:
            year_val = int(digits[-4:])
            assert 2020 <= year_val <= 2024

    # Invalid year range
    response = client.get("/api/v1/companies/TCS/pl?from_year=2024&to_year=2020")
    assert response.status_code == 400


def test_get_company_bs():
    """Verify GET /api/v1/companies/{ticker}/bs historical endpoint and filters."""
    # Valid bs
    response = client.get("/api/v1/companies/TCS/bs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "equity_capital" in data[0]
    assert "total_assets" in data[0]

    # Invalid year range
    response = client.get("/api/v1/companies/TCS/bs?from_year=2024&to_year=2020")
    assert response.status_code == 400


def test_get_company_cashflow():
    """Verify GET /api/v1/companies/{ticker}/cashflow historical endpoint and filters."""
    # Valid cashflow
    response = client.get("/api/v1/companies/TCS/cashflow")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "operating_activity" in data[0]
    assert "net_cash_flow" in data[0]

    # Invalid year range
    response = client.get("/api/v1/companies/TCS/cashflow?from_year=2024&to_year=2020")
    assert response.status_code == 400


def test_get_company_ratios():
    """Verify GET /api/v1/companies/{ticker}/ratios and year filter."""
    response = client.get("/api/v1/companies/TCS/ratios")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "net_profit_margin_pct" in data[0]
    assert "icr_label" in data[0]

    # Year filter
    response = client.get("/api/v1/companies/TCS/ratios?year=2024")
    assert response.status_code == 200
    for r in response.json():
        assert "2024" in r["year"]


def test_get_company_tearsheet():
    """Verify GET /api/v1/companies/{ticker}/tearsheet download."""
    # Valid tearsheet
    response = client.get("/api/v1/companies/TCS/tearsheet")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

    # Missing tearsheet/invalid ticker
    response = client.get("/api/v1/companies/INVALID/tearsheet")
    assert response.status_code == 404
