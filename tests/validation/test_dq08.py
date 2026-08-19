import pandas as pd

from src.validation.dq_rules import validate_dq08_ticker_format
from src.validation.report import ValidationReport


def test_dq08_valid_ticker():
    dfs = {
        "companies": pd.DataFrame({"id": ["ABB", "TCS", "M&M"]}),
        "profitandloss": pd.DataFrame({"company_id": ["ABB", "TCS", "M&M"]}),
    }
    report = ValidationReport()
    validate_dq08_ticker_format(dfs, report)
    assert len(report.failures) == 0


def test_dq08_invalid_ticker():
    dfs = {
        "companies": pd.DataFrame(
            {"id": ["abb", "TCS_LONG_TICKER_X"]}
        ),  # Lowercase and too long
        "profitandloss": pd.DataFrame(
            {"company_id": ["A", "TCS.NS"]}
        ),  # Too short and invalid character (dot)
    }
    report = ValidationReport()
    validate_dq08_ticker_format(dfs, report)
    # 2 in companies, 2 in profitandloss
    assert len(report.failures) == 4
    assert all(f.rule_id == "DQ-08" for f in report.failures)
    assert all(f.severity == "CRITICAL" for f in report.failures)
