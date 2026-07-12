import pandas as pd
from src.validation.report import ValidationReport
from src.validation.dq_rules import validate_dq02_no_duplicate_company_year


def test_dq02_no_duplicates():
    dfs = {
        "profitandloss": pd.DataFrame(
            {"company_id": ["ABB", "TCS"], "year": ["2023-03", "2023-03"]}
        ),
        "balancesheet": pd.DataFrame(
            {"company_id": ["ABB", "TCS"], "year": ["2023-03", "2023-03"]}
        ),
        "cashflow": pd.DataFrame(
            {"company_id": ["ABB", "TCS"], "year": ["2023-03", "2023-03"]}
        ),
    }
    report = ValidationReport()
    validate_dq02_no_duplicate_company_year(dfs, report)
    assert len(report.failures) == 0


def test_dq02_with_duplicates():
    dfs = {
        "profitandloss": pd.DataFrame(
            {
                "company_id": ["ABB", "ABB", "TCS"],
                "year": ["2023-03", "2023-03", "2023-03"],
            }
        ),
        "balancesheet": pd.DataFrame(
            {"company_id": ["ABB", "TCS"], "year": ["2023-03", "2023-03"]}
        ),
        "cashflow": pd.DataFrame(
            {"company_id": ["TCS", "TCS"], "year": ["2023-03", "2023-03"]}
        ),
    }
    report = ValidationReport()
    validate_dq02_no_duplicate_company_year(dfs, report)
    # profitandloss has 2 duplicate rows for ABB, cashflow has 2 duplicate rows for TCS
    assert len(report.failures) == 4
    assert all(f.rule_id == "DQ-02" for f in report.failures)
    assert all(f.severity == "CRITICAL" for f in report.failures)
