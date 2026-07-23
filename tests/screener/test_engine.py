import pandas as pd

from src.screener.engine import filter_companies, load_screener_config


def test_load_screener_config_reads_thresholds():
    config = load_screener_config()
    assert config["filters"]["min_roe"] == 15
    assert config["filters"]["max_debt_to_equity"] == 1


def test_filter_companies_applies_exceptions_and_sorts_results():
    df = pd.DataFrame(
        [
            {
                "company_id": "ALPHA",
                "sector": "Industrials",
                "return_on_equity_pct": 18.0,
                "debt_to_equity": 0.8,
                "free_cash_flow_cr": 5.0,
                "revenue_cagr_5yr": 12.0,
                "pat_cagr_5yr": 12.0,
                "operating_profit_margin_pct": 12.0,
                "pe": 18.0,
                "pb": 1.4,
                "dividend_yield": 1.5,
                "interest_coverage": 3.0,
                "market_cap": 150.0,
                "net_profit": 80.0,
                "eps_cagr_5yr": 9.0,
                "asset_turnover": 1.2,
                "sales": 500.0,
                "icr_label": "Healthy",
                "composite_quality_score": 72.0,
            },
            {
                "company_id": "BETA",
                "sector": "Financials",
                "return_on_equity_pct": 20.0,
                "debt_to_equity": 3.0,
                "free_cash_flow_cr": 6.0,
                "revenue_cagr_5yr": 13.0,
                "pat_cagr_5yr": 13.0,
                "operating_profit_margin_pct": 13.0,
                "pe": 16.0,
                "pb": 1.1,
                "dividend_yield": 2.0,
                "interest_coverage": 4.0,
                "market_cap": 200.0,
                "net_profit": 90.0,
                "eps_cagr_5yr": 10.0,
                "asset_turnover": 1.5,
                "sales": 600.0,
                "icr_label": "Healthy",
                "composite_quality_score": 81.0,
            },
            {
                "company_id": "GAMMA",
                "sector": "Industrials",
                "return_on_equity_pct": 21.0,
                "debt_to_equity": 1.2,
                "free_cash_flow_cr": 7.0,
                "revenue_cagr_5yr": 14.0,
                "pat_cagr_5yr": 14.0,
                "operating_profit_margin_pct": 14.0,
                "pe": 15.0,
                "pb": 1.0,
                "dividend_yield": 2.5,
                "interest_coverage": 1.0,
                "market_cap": 250.0,
                "net_profit": 100.0,
                "eps_cagr_5yr": 11.0,
                "asset_turnover": 1.6,
                "sales": 700.0,
                "icr_label": "Debt Free",
                "composite_quality_score": 95.0,
            },
            {
                "company_id": "DELTA",
                "sector": "Industrials",
                "return_on_equity_pct": 8.0,
                "debt_to_equity": 0.2,
                "free_cash_flow_cr": 4.0,
                "revenue_cagr_5yr": 11.0,
                "pat_cagr_5yr": 11.0,
                "operating_profit_margin_pct": 11.0,
                "pe": 30.0,
                "pb": 2.0,
                "dividend_yield": 0.5,
                "interest_coverage": 2.0,
                "market_cap": 50.0,
                "net_profit": 20.0,
                "eps_cagr_5yr": 7.0,
                "asset_turnover": 0.5,
                "sales": 100.0,
                "icr_label": "Healthy",
                "composite_quality_score": 40.0,
            },
        ]
    )

    config = {
        "filters": {
            "min_roe": 15,
            "max_debt_to_equity": 1,
            "min_fcf": 0,
            "min_revenue_cagr_5yr": 10,
            "min_pat_cagr_5yr": 10,
            "min_operating_profit_margin": 10,
            "max_pe": 20,
            "max_pb": 1.5,
            "min_dividend_yield": 1,
            "min_interest_coverage": 2,
            "min_market_cap": 100,
            "min_net_profit": 50,
            "min_eps_cagr_5yr": 8,
            "min_asset_turnover": 1,
            "min_sales": 200,
        }
    }

    result = filter_companies(df, config)

    assert list(result["company_id"]) == ["BETA", "ALPHA"]
    assert set(result["company_id"]) == {"BETA", "ALPHA"}
