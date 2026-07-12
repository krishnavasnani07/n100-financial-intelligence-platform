import pandas as pd
from src.validation.report import ValidationReport
from src.validation.dq_rules import validate_dq01_company_pk


def test_dq01_no_duplicates():
    df = pd.DataFrame({"id": ["ABB", "TCS", "INFY"]})
    report = ValidationReport()
    validate_dq01_company_pk(df, report)
    assert len(report.failures) == 0


def test_dq01_with_duplicates():
    df = pd.DataFrame({"id": ["ABB", "TCS", "ABB", "INFY"]})
    report = ValidationReport()
    validate_dq01_company_pk(df, report)
    assert len(report.failures) == 2  # Both duplicate ABB rows flagged
    assert all(f.rule_id == "DQ-01" for f in report.failures)
    assert all(f.severity == "CRITICAL" for f in report.failures)
    assert report.failures[0].company_id == "ABB"
