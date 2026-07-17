"""
Unit test for automated financial ratio spot-check verification engine.
"""

import pytest
import pandas as pd
from pathlib import Path
from src.config.settings import BASE_DIR
from scripts.verify_ratios import run_spot_check_verification

def test_spot_check_verification(tmp_path):
    db_path = BASE_DIR / "db" / "nifty100.db"
    if not db_path.exists():
        pytest.skip("SQLite database nifty100.db not found for integration test.")

    df_res = run_spot_check_verification(db_path, tmp_path)
    assert not df_res.empty
    assert "npm_match" in df_res.columns
    assert df_res["npm_match"].mean() == 1.0
    assert df_res["opm_match"].mean() == 1.0
    assert df_res["roe_match"].mean() == 1.0
    assert df_res["roce_match"].mean() == 1.0
    assert df_res["roa_match"].mean() == 1.0

    report_file = tmp_path / "ratio_spot_check.csv"
    assert report_file.exists()
