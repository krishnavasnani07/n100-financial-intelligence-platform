import pandas as pd
from src.validation.report import ValidationReport
from src.validation.dq_rules import validate_dq03_foreign_keys


def test_dq03_valid_fk():
    dfs = {
        "companies": pd.DataFrame({"id": ["ABB", "TCS"]}),
        "profitandloss": pd.DataFrame(
            {"company_id": ["ABB", "TCS"], "year": ["2023-03", "2023-03"]}
        ),
        "balancesheet": pd.DataFrame({"company_id": ["ABB"], "year": ["2023-03"]}),
    }
    report = ValidationReport()
    validate_dq03_foreign_keys(dfs, report)
    assert len(report.failures) == 0


def test_dq03_invalid_fk():
    dfs = {
        "companies": pd.DataFrame({"id": ["ABB", "TCS"]}),
        "profitandloss": pd.DataFrame(
            {"company_id": ["ABB", "INVALID_TICKER"], "year": ["2023-03", "2023-03"]}
        ),
        "balancesheet": pd.DataFrame({"company_id": ["XYZ"], "year": ["2023-03"]}),
    }
    report = ValidationReport()
    validate_dq03_foreign_keys(dfs, report)
    # One in profitandloss (INVALID_TICKER), one in balancesheet (XYZ)
    assert len(report.failures) == 2
    assert all(f.rule_id == "DQ-03" for f in report.failures)
    assert all(f.severity == "CRITICAL" for f in report.failures)
