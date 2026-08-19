from pathlib import Path

from src.etl.loader import load_excel
from src.validation.dq_rules import (
    validate_dq01_company_pk,
    validate_dq04_balancesheet_balance,
    validate_dq06_positive_sales,
    validate_dq07_year_format,
    validate_dq08_ticker_format,
)
from src.validation.report import ValidationReport

test_data_dir = Path(__file__).resolve().parent.parent / "data"


def test_mock_duplicate_companies():
    # Header at row 1
    df = load_excel(
        test_data_dir / "duplicate_company.xlsx", sheet_name="Companies", header=1
    )
    # Clean column headers
    df.columns = [str(col).strip() for col in df.columns]
    report = ValidationReport()
    validate_dq01_company_pk(df, report)
    # Expect 2 duplicate rows for ABB
    assert len(report.failures) == 2
    assert all(f.company_id == "ABB" for f in report.failures)


def test_mock_invalid_years():
    df = load_excel(
        test_data_dir / "invalid_year.xlsx", sheet_name="Profit & Loss", header=1
    )
    df.columns = [str(col).strip() for col in df.columns]
    report = ValidationReport()
    dfs = {"profitandloss": df}
    validate_dq07_year_format(dfs, report)
    # 'TTM' and 'Mar 2016 9m' should fail normalization. 'Mar-23' and '2023-03' should pass.
    assert len(report.failures) == 2
    failed_years = [f.year for f in report.failures]
    assert "TTM" in failed_years
    assert "Mar 2016 9m" in failed_years


def test_mock_invalid_tickers():
    df = load_excel(
        test_data_dir / "invalid_ticker.xlsx", sheet_name="Companies", header=1
    )
    df.columns = [str(col).strip() for col in df.columns]
    report = ValidationReport()
    dfs = {"companies": df}
    validate_dq08_ticker_format(dfs, report)
    # 'A' (too short), 'TCS_INVALID_LONG' (too long), 'TCS.NS' (invalid char) should fail
    assert len(report.failures) == 3
    failed_ids = [f.company_id for f in report.failures]
    assert "A" in failed_ids
    assert "TCS_INVALID_LONG" in failed_ids
    assert "TCS.NS" in failed_ids


def test_mock_negative_sales():
    df = load_excel(
        test_data_dir / "negative_sales.xlsx", sheet_name="Profit & Loss", header=1
    )
    df.columns = [str(col).strip() for col in df.columns]
    report = ValidationReport()
    validate_dq06_positive_sales(df, report)
    # -50.0 should fail
    assert len(report.failures) == 1
    assert report.failures[0].company_id == "TCS"
    assert float(report.failures[0].raw_value) == -50.0


def test_mock_balancesheet_mismatch():
    df = load_excel(
        test_data_dir / "balancesheet_mismatch.xlsx",
        sheet_name="Balance Sheet",
        header=1,
    )
    df.columns = [str(col).strip() for col in df.columns]
    report = ValidationReport()
    validate_dq04_balancesheet_balance(df, report)
    # 150.0 vs 120.0 should fail
    assert len(report.failures) == 1
    assert report.failures[0].company_id == "TCS"
