"""
Unit and Integration Tests for Financial Ratio Population Engine (Sprint 2 - Day 12).
"""

import sqlite3
import pytest
import pandas as pd
from pathlib import Path

from src.config.settings import DB_PATH, OUTPUT_DIR
from src.analytics.populate_financial_ratios import (
    extract_year_int,
    calculate_composite_quality_score,
    populate_ratios_pipeline,
    verify_spot_checks,
)


def test_extract_year_int():
    """Test calendar year parsing from financial year strings."""
    assert extract_year_int("Mar 2024") == 2024
    assert extract_year_int("Dec 2018") == 2018
    assert extract_year_int("2020") == 2020
    assert extract_year_int("TTM") is None
    assert extract_year_int(None) is None


def test_calculate_composite_quality_score():
    """Test Composite Quality Score calculation under various financial scenarios."""
    # Scenario A: Top Tier Performer
    score_a = calculate_composite_quality_score(
        roe=25.0, roce=25.0, rev_cagr=20.0, pat_cagr=20.0, de_ratio=0.1, icr=15.0, cfo_quality=1.2
    )
    assert score_a == 100.0

    # Scenario B: Average Performer
    score_b = calculate_composite_quality_score(
        roe=10.0, roce=10.0, rev_cagr=7.5, pat_cagr=7.5, de_ratio=1.25, icr=5.5, cfo_quality=0.5
    )
    assert pytest.approx(score_b, 0.1) == 50.0

    # Scenario C: Poor / Distressed Performer
    score_c = calculate_composite_quality_score(
        roe=-5.0, roce=-5.0, rev_cagr=-10.0, pat_cagr=-10.0, de_ratio=3.0, icr=0.5, cfo_quality=-0.2
    )
    assert score_c == 0.0

    # Scenario D: Missing CAGR (e.g. recent IPO)
    score_d = calculate_composite_quality_score(
        roe=20.0, roce=20.0, rev_cagr=None, pat_cagr=None, de_ratio=0.0, icr=None, cfo_quality=1.0
    )
    assert score_d == 100.0


def test_populate_ratios_pipeline_execution():
    """Test end-to-end population of financial_ratios SQLite table and CSV export."""
    df_ratios = populate_ratios_pipeline(DB_PATH)

    # 1. Row count validation
    assert len(df_ratios) >= 1100

    # 2. SQLite Database Table Check
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM financial_ratios")
    db_count = cursor.fetchone()[0]
    conn.close()

    assert db_count == len(df_ratios)
    assert db_count >= 1100

    # 3. CSV File Validation
    csv_file = OUTPUT_DIR / "financial_ratios.csv"
    assert csv_file.exists()

    df_csv = pd.read_csv(csv_file)
    assert len(df_csv) == db_count

    # 4. Null Column Validation (No KPI column should be 100% NULL)
    kpi_cols = [
        "net_profit_margin_pct", "operating_profit_margin_pct", "return_on_equity_pct",
        "return_on_capital_employed_pct", "return_on_assets_pct", "debt_to_equity",
        "interest_coverage", "asset_turnover", "free_cash_flow_cr", "capex_cr",
        "earnings_per_share", "book_value_per_share", "dividend_payout_ratio_pct",
        "total_debt_cr", "cash_from_operations_cr", "composite_quality_score"
    ]

    for col in kpi_cols:
        null_count = df_ratios[col].isnull().sum()
        assert null_count < len(df_ratios), f"Column {col} is 100% NULL"
