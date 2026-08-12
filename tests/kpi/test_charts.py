"""
Unit test for automated financial ratio visual distribution generator.
"""

import pytest
from pathlib import Path
from src.config.settings import BASE_DIR
from src.analytics.charts import generate_profitability_charts


def test_generate_profitability_charts(tmp_path):
    log_csv = BASE_DIR / "output" / "ratio_calculation_log.csv"
    if not log_csv.exists():
        pytest.skip("ratio_calculation_log.csv not found for integration test.")

    out_file = generate_profitability_charts(log_csv, tmp_path)
    assert out_file.exists()
    assert out_file.stat().st_size > 0
