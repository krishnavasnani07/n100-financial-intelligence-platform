import pandas as pd
from src.validation.report import ValidationReport
from src.validation.dq_rules import validate_dq07_year_format


def test_dq07_valid_year():
    dfs = {
        "profitandloss": pd.DataFrame({"company_id": ["ABB"], "year": ["2023-03"]}),
        "balancesheet": pd.DataFrame(
            {"company_id": ["ABB"], "year": ["Mar-23"]}
        ),  # Normalizable to '2023-03'
    }
    report = ValidationReport()
    validate_dq07_year_format(dfs, report)
    assert len(report.failures) == 0


def test_dq07_invalid_year():
    dfs = {
        "profitandloss": pd.DataFrame(
            {"company_id": ["ABB"], "year": ["2023-13"]}
        ),  # Invalid month after normalization
        "balancesheet": pd.DataFrame(
            {"company_id": ["ABB"], "year": ["garbage"]}
        ),  # Non-normalizable
    }
    report = ValidationReport()
    validate_dq07_year_format(dfs, report)
    assert len(report.failures) == 2
    assert all(f.rule_id == "DQ-07" for f in report.failures)
    assert all(f.severity == "CRITICAL" for f in report.failures)
