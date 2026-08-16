import pytest
import pandas as pd
from typing import Dict
from src.validation.report import ValidationReport
from src.validation.dq_rules import (
    validate_dq01_company_pk,
    validate_dq02_no_duplicate_company_year,
    validate_dq03_foreign_keys,
    validate_dq04_balancesheet_balance,
    validate_dq05_opm_crosscheck,
    validate_dq06_positive_sales,
    validate_dq07_year_format,
    validate_dq08_ticker_format,
    validate_dq09_net_cash_flow,
    validate_dq10_fixed_assets,
    validate_dq11_tax_rate,
    validate_dq12_dividend_payout,
    validate_dq13_url_validation,
    validate_dq14_eps_sign
)

@pytest.fixture
def valid_datasets() -> Dict[str, pd.DataFrame]:
    df_companies = pd.DataFrame([
        {
            "id": "TCS",
            "company_name": "Tata Consultancy Services",
            "company_logo": "https://tcs.com/logo.png",
            "chart_link": "https://tcs.com/chart",
            "website": "https://tcs.com",
            "nse_profile": "https://nse.com/tcs",
            "bse_profile": "https://bse.com/tcs"
        }
    ])
    
    df_pl = pd.DataFrame([
        {
            "company_id": "TCS",
            "year": "2023-03",
            "sales": 100.0,
            "operating_profit": 20.0,
            "opm_percentage": 20.0,
            "tax_percentage": 25.0,
            "dividend_payout": 30.0,
            "net_profit": 15.0,
            "eps": 12.0
        }
    ])
    
    df_bs = pd.DataFrame([
        {
            "company_id": "TCS",
            "year": "2023-03",
            "total_assets": 500.0,
            "total_liabilities": 500.0,
            "fixed_assets": 200.0,
            "cwip": 50.0,
            "investments": 100.0,
            "other_asset": 150.0,
            "equity_capital": 100.0,
            "reserves": 200.0,
            "borrowings": 100.0,
            "other_liabilities": 100.0
        }
    ])
    
    df_cf = pd.DataFrame([
        {
            "company_id": "TCS",
            "year": "2023-03",
            "operating_activity": 120.0,
            "investing_activity": -50.0,
            "financing_activity": -30.0,
            "net_cash_flow": 40.0
        }
    ])
    
    df_docs = pd.DataFrame([
        {
            "company_id": "TCS",
            "Year": "2023-03",
            "Annual_Report": "https://tcs.com/ar2023.pdf"
        }
    ])
    
    return {
        "companies": df_companies,
        "profitandloss": df_pl,
        "balancesheet": df_bs,
        "cashflow": df_cf,
        "documents": df_docs
    }

# 1. DQ-01: Company PK uniqueness
def test_dq01_company_pk(valid_datasets):
    df_c = valid_datasets["companies"].copy()
    # Add duplicate id row
    df_c.loc[1] = {
        "id": "TCS",
        "company_name": "Duplicate TCS",
        "company_logo": "https://tcs.com/logo2.png",
        "chart_link": "https://tcs.com/chart2",
        "website": "https://tcs.com",
        "nse_profile": "https://nse.com/tcs",
        "bse_profile": "https://bse.com/tcs"
    }
    
    report = ValidationReport()
    validate_dq01_company_pk(df_c, report)
    
    assert len(report.failures) == 2  # Both rows are marked as duplicate PK
    assert report.failures[0].rule_id == "DQ-01"
    assert report.failures[0].severity == "CRITICAL"

# 2. DQ-02: Duplicate company_id and year
def test_dq02_no_duplicate_company_year(valid_datasets):
    dfs = {k: v.copy() for k, v in valid_datasets.items()}
    # Add duplicate year row to profitandloss
    df_pl = dfs["profitandloss"]
    df_pl.loc[1] = {
        "company_id": "TCS",
        "year": "2023-03",
        "sales": 120.0,
        "operating_profit": 24.0,
        "opm_percentage": 20.0,
        "tax_percentage": 25.0,
        "dividend_payout": 30.0,
        "net_profit": 18.0,
        "eps": 14.0
    }
    
    report = ValidationReport()
    validate_dq02_no_duplicate_company_year(dfs, report)
    
    assert len(report.failures) == 2
    assert report.failures[0].rule_id == "DQ-02"
    assert report.failures[0].severity == "CRITICAL"

# 3. DQ-03: Foreign Key integrity
def test_dq03_foreign_keys(valid_datasets):
    dfs = {k: v.copy() for k, v in valid_datasets.items()}
    # Introduce invalid FK in profitandloss
    dfs["profitandloss"].loc[0, "company_id"] = "INFY"  # INFY is not in companies table
    
    report = ValidationReport()
    validate_dq03_foreign_keys(dfs, report)
    
    assert len(report.failures) == 1
    assert report.failures[0].rule_id == "DQ-03"
    assert report.failures[0].severity == "CRITICAL"

# 4. DQ-04: Balance Sheet does not balance
def test_dq04_balancesheet_balance(valid_datasets):
    df_bs = valid_datasets["balancesheet"].copy()
    # Modify total_liabilities so it doesn't match total_assets (500)
    df_bs.loc[0, "total_liabilities"] = 490.0
    
    report = ValidationReport()
    validate_dq04_balancesheet_balance(df_bs, report)
    
    assert len(report.failures) == 1
    assert report.failures[0].rule_id == "DQ-04"
    assert report.failures[0].severity == "WARNING"

# 5. DQ-05: OPM cross-check mismatch
def test_dq05_opm_crosscheck(valid_datasets):
    df_pl = valid_datasets["profitandloss"].copy()
    # Sales = 100, Operating Profit = 20, but OPM = 50.0 (mismatch)
    df_pl.loc[0, "opm_percentage"] = 50.0
    
    report = ValidationReport()
    validate_dq05_opm_crosscheck(df_pl, report)
    
    assert len(report.failures) == 1
    assert report.failures[0].rule_id == "DQ-05"
    assert report.failures[0].severity == "WARNING"

# 6. DQ-06: Non-positive sales
def test_dq06_positive_sales(valid_datasets):
    df_pl = valid_datasets["profitandloss"].copy()
    df_pl.loc[0, "sales"] = -10.0
    
    report = ValidationReport()
    validate_dq06_positive_sales(df_pl, report)
    
    assert len(report.failures) == 1
    assert report.failures[0].rule_id == "DQ-06"
    assert report.failures[0].severity == "WARNING"

# 7. DQ-07: Year format violation
def test_dq07_year_format(valid_datasets):
    dfs = {k: v.copy() for k, v in valid_datasets.items()}
    dfs["profitandloss"].loc[0, "year"] = "invalid_year_format"
    
    report = ValidationReport()
    validate_dq07_year_format(dfs, report)
    
    assert len(report.failures) == 1
    assert report.failures[0].rule_id == "DQ-07"
    assert report.failures[0].severity == "CRITICAL"

# 8. DQ-08: Ticker format violation
def test_dq08_ticker_format(valid_datasets):
    dfs = {k: v.copy() for k, v in valid_datasets.items()}
    dfs["companies"].loc[0, "id"] = "A"  # Too short
    
    report = ValidationReport()
    validate_dq08_ticker_format(dfs, report)
    
    assert len(report.failures) == 1
    assert report.failures[0].rule_id == "DQ-08"
    assert report.failures[0].severity == "CRITICAL"

# 9. DQ-09: Net Cash Flow mismatch
def test_dq09_net_cash_flow(valid_datasets):
    df_cf = valid_datasets["cashflow"].copy()
    # Op=120, Inv=-50, Fin=-30. Sum should be 40, but reported is 50
    df_cf.loc[0, "net_cash_flow"] = 50.0
    
    report = ValidationReport()
    validate_dq09_net_cash_flow(df_cf, report)
    
    assert len(report.failures) == 1
    assert report.failures[0].rule_id == "DQ-09"
    assert report.failures[0].severity == "WARNING"

# 10. DQ-10: Fixed Assets validation
def test_dq10_fixed_assets(valid_datasets):
    df_bs = valid_datasets["balancesheet"].copy()
    # Fixed Assets (600) exceeds Total Assets (500)
    df_bs.loc[0, "fixed_assets"] = 600.0
    
    report = ValidationReport()
    validate_dq10_fixed_assets(df_bs, report)
    
    assert len(report.failures) == 1
    assert report.failures[0].rule_id == "DQ-10"
    assert report.failures[0].severity == "WARNING"

# 11. DQ-11: Tax rate out of bounds
def test_dq11_tax_rate(valid_datasets):
    df_pl = valid_datasets["profitandloss"].copy()
    df_pl.loc[0, "tax_percentage"] = 120.0  # > 100%
    
    report = ValidationReport()
    validate_dq11_tax_rate(df_pl, report)
    
    assert len(report.failures) == 1
    assert report.failures[0].rule_id == "DQ-11"
    assert report.failures[0].severity == "WARNING"

# 12. DQ-12: Dividend payout out of bounds
def test_dq12_dividend_payout(valid_datasets):
    df_pl = valid_datasets["profitandloss"].copy()
    df_pl.loc[0, "dividend_payout"] = 1005.0  # Exceeds max payout ratio limit
    
    report = ValidationReport()
    validate_dq12_dividend_payout(df_pl, report)
    
    assert len(report.failures) == 1
    assert report.failures[0].rule_id == "DQ-12"
    assert report.failures[0].severity == "WARNING"

# 13. DQ-13: URL validation failure
def test_dq13_url_validation(valid_datasets):
    dfs = {k: v.copy() for k, v in valid_datasets.items()}
    dfs["companies"].loc[0, "website"] = "not_a_valid_url"
    
    report = ValidationReport()
    validate_dq13_url_validation(dfs, report)
    
    assert len(report.failures) == 1
    assert report.failures[0].rule_id == "DQ-13"
    assert report.failures[0].severity == "WARNING"

# 14. DQ-14: EPS sign mismatch
def test_dq14_eps_sign(valid_datasets):
    df_pl = valid_datasets["profitandloss"].copy()
    # Net Profit is positive (15.0), but EPS is negative (-2.0)
    df_pl.loc[0, "eps"] = -2.0
    
    report = ValidationReport()
    validate_dq14_eps_sign(df_pl, report)
    
    assert len(report.failures) == 1
    assert report.failures[0].rule_id == "DQ-14"
    assert report.failures[0].severity == "WARNING"
