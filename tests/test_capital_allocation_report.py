"""
Unit tests for the Capital Allocation Intelligence & Strategy Evolution module.
Verifies transition classification, validation checking, and report generation.
"""

from pathlib import Path

import pandas as pd

from src.analytics.capital_allocation_report import (
    categorize_transition,
    run_capital_allocation_report,
    verify_capital_allocation,
)
from src.config.settings import DB_PATH


def test_categorize_transition():
    """Verify strategy transition categorization rules."""
    # Direct examples
    assert categorize_transition("Reinvestor", "Shareholder Returns") == "Mature"
    assert (
        categorize_transition("Growth Funded by Debt", "Distress Signal")
        == "Negative Shift"
    )
    assert categorize_transition("Distress Signal", "Cash Accumulator") == "Recovery"
    assert categorize_transition("Mixed", "Reinvestor") == "Improving"

    # Same pattern
    assert categorize_transition("Reinvestor", "Reinvestor") == "No Change"

    # Generic shift
    assert categorize_transition("Pre-Revenue", "Mixed") == "Strategic Shift"


def test_verify_capital_allocation():
    """Verify validation functions detect duplicate entries and invalid patterns."""
    # Create valid mock dataframe
    df_valid = pd.DataFrame(
        [
            {"company_id": "ABB", "year": "Mar 2024", "pattern_label": "Reinvestor"},
            {
                "company_id": "TCS",
                "year": "Mar 2024",
                "pattern_label": "Shareholder Returns",
            },
        ]
    )

    # This should fail company count check since len is 2 instead of 92
    errors = verify_capital_allocation(df_valid, DB_PATH)
    assert any("Expected 92 companies" in err for err in errors)

    # Test duplicate detection
    df_dup = pd.DataFrame(
        [
            {"company_id": "ABB", "year": "Mar 2024", "pattern_label": "Reinvestor"},
            {
                "company_id": "ABB",
                "year": "Mar 2024",
                "pattern_label": "Shareholder Returns",
            },
        ]
        * 46
    )  # Repeat to get 92 rows
    errors_dup = verify_capital_allocation(df_dup, DB_PATH)
    assert any("Duplicate" in err for err in errors_dup)

    # Test invalid patterns
    df_invalid = pd.DataFrame(
        [
            {
                "company_id": "ABB",
                "year": "Mar 2024",
                "pattern_label": "InvalidPattern",
            },
        ]
        * 92
    )
    errors_inv = verify_capital_allocation(df_invalid, DB_PATH)
    assert any("Invalid pattern labels" in err for err in errors_inv)


def test_pipeline_execution(tmp_path):
    """Verify that run_capital_allocation_report executes and generates outputs."""
    # Write a copy of capital_allocation.csv to tmp_path first
    orig_csv = Path("output/capital_allocation.csv")
    if orig_csv.exists():
        tmp_csv = tmp_path / "capital_allocation.csv"
        tmp_csv.write_bytes(orig_csv.read_bytes())

        # Write dummy cashflow_intelligence.xlsx so it can be updated
        orig_xlsx = Path("output/cashflow_intelligence.xlsx")
        if orig_xlsx.exists():
            tmp_xlsx = tmp_path / "cashflow_intelligence.xlsx"
            tmp_xlsx.write_bytes(orig_xlsx.read_bytes())

        res = run_capital_allocation_report(db_path=DB_PATH, output_dir=tmp_path)

        assert "summary" in res
        assert "changes" in res
        assert (tmp_path / "capital_allocation_summary.csv").exists()
        assert (tmp_path / "pattern_changes.csv").exists()

        # Check cashflow_intelligence.xlsx was updated
        df_excel = pd.read_excel(tmp_path / "cashflow_intelligence.xlsx")
        assert "Capital Allocation" in df_excel.columns
