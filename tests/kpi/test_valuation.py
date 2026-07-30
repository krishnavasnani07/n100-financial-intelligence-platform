"""
Unit tests for the Valuation Engine.
"""

import pytest
import pandas as pd
from pathlib import Path
from src.config.settings import BASE_DIR, DB_PATH
from src.analytics.valuation import run_valuation_pipeline


def test_valuation_pipeline():
    if not DB_PATH.exists():
        pytest.skip("SQLite database not found for valuation integration test.")

    # Run the pipeline
    df_val = run_valuation_pipeline()

    # Validations
    assert not df_val.empty
    
    # 92 Nifty 100 companies expected
    assert len(df_val) == 92 or len(df_val) == 93  # Handle minor database variance

    # Check required columns
    expected_cols = [
        "company_id", "company_name", "sector", "PE", "PB", "EV/EBITDA",
        "FCF_yield_pct", "5yr_median_PE", "PE_vs_sector_median_pct", "flag"
    ]
    for col in expected_cols:
        assert col in df_val.columns

    # Check flag values
    assert df_val["flag"].isin(["Discount", "Fair", "Caution"]).all()

    # Check export paths
    summary_xlsx = BASE_DIR / "output" / "valuation_summary.xlsx"
    flags_csv = BASE_DIR / "output" / "valuation_flags.csv"
    valuation_log = BASE_DIR / "logs" / "valuation.log"

    assert summary_xlsx.exists()
    assert flags_csv.exists()
    assert valuation_log.exists()

    # Verify CSV flags report contains only Discount and Caution
    df_csv = pd.read_csv(flags_csv)
    assert df_csv["Flag"].isin(["Discount", "Caution"]).all()
    assert "Company" in df_csv.columns
    assert "Sector" in df_csv.columns
    assert "PE" in df_csv.columns
    assert "Sector Median" in df_csv.columns
    assert "FCF Yield" in df_csv.columns
