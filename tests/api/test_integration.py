from fastapi.testclient import TestClient

from src.api.main import app
from src.screener.engine import filter_companies
from src.screener.presets import load_screener_master_data

client = TestClient(app)


def test_integration_screener_min_roe():
    """Verify that Streamlit dashboard logic and API screener return the same companies for min_roe=15."""
    # 1. API Results
    api_res = client.get("/api/v1/screener?min_roe=15")
    assert api_res.status_code == 200
    api_tickers = sorted([comp["ticker"] for comp in api_res.json()])

    # 2. Dashboard Logic Results
    df_master = load_screener_master_data()
    filters_config = {"min_roe": 15.0}
    df_filtered = filter_companies(df_master, {"filters": filters_config})
    dashboard_tickers = sorted(df_filtered["company_id"].tolist())

    # 3. Assert Consistency
    assert len(api_tickers) > 0
    assert api_tickers == dashboard_tickers


def test_integration_screener_max_debt():
    """Verify that Streamlit dashboard logic and API screener return the same companies for max debt to equity ratio."""
    # 1. API Results (max_de maps to max_debt_to_equity in dashboard)
    api_res = client.get("/api/v1/screener?max_de=0.8")
    assert api_res.status_code == 200
    api_tickers = sorted([comp["ticker"] for comp in api_res.json()])

    # 2. Dashboard Logic Results
    df_master = load_screener_master_data()
    filters_config = {"max_debt_to_equity": 0.8}
    df_filtered = filter_companies(df_master, {"filters": filters_config})
    dashboard_tickers = sorted(df_filtered["company_id"].tolist())

    # 3. Assert Consistency
    assert len(api_tickers) > 0
    assert api_tickers == dashboard_tickers


def test_integration_screener_min_fcf():
    """Verify that Streamlit dashboard logic and API screener return the same companies for min FCF."""
    # 1. API Results
    api_res = client.get("/api/v1/screener?min_fcf=200")
    assert api_res.status_code == 200
    api_tickers = sorted([comp["ticker"] for comp in api_res.json()])

    # 2. Dashboard Logic Results
    df_master = load_screener_master_data()
    filters_config = {"min_fcf": 200.0}
    df_filtered = filter_companies(df_master, {"filters": filters_config})
    dashboard_tickers = sorted(df_filtered["company_id"].tolist())

    # 3. Assert Consistency
    assert len(api_tickers) > 0
    assert api_tickers == dashboard_tickers


def test_integration_screener_combined():
    """Verify that Streamlit dashboard logic and API screener return the same companies for combined filters."""
    # 1. API Results
    api_res = client.get("/api/v1/screener?min_roe=15&max_de=0.5&min_fcf=100")
    assert api_res.status_code == 200
    api_tickers = sorted([comp["ticker"] for comp in api_res.json()])

    # 2. Dashboard Logic Results
    df_master = load_screener_master_data()
    filters_config = {"min_roe": 15.0, "max_debt_to_equity": 0.5, "min_fcf": 100.0}
    df_filtered = filter_companies(df_master, {"filters": filters_config})
    dashboard_tickers = sorted(df_filtered["company_id"].tolist())

    # 3. Assert Consistency
    assert api_tickers == dashboard_tickers
