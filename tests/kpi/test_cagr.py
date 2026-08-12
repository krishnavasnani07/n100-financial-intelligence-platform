"""
Unit and integration tests for Growth Analytics CAGR Engine (Sprint 2 - Day 10).
Verifies generic CAGR calculations, 6 financial edge cases, growth classification,
multi-year company batch processing, logging, and CSV report exports.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.analytics.cagr import (
    calculate_cagr,
    classify_growth_cagr,
    CAGRResult,
    CAGREngine,
)
from src.config.growth_config import (
    FLAG_VALID,
    FLAG_DECLINE_TO_LOSS,
    FLAG_TURNAROUND,
    FLAG_BOTH_NEGATIVE,
    FLAG_ZERO_BASE,
    FLAG_INSUFFICIENT,
    FLAG_INVALID_INPUT,
    LABEL_HIGH_GROWTH,
    LABEL_STRONG_GROWTH,
    LABEL_MODERATE_GROWTH,
    LABEL_SLOW_GROWTH,
    LABEL_DECLINING,
    LABEL_NOT_APPLICABLE,
)


class TestGenericCAGREngine:
    def test_calculate_cagr_valid_revenue(self):
        cagr, flag = calculate_cagr(
            start_value=100, end_value=200, years=5, metric_name="Revenue"
        )
        assert cagr == 14.87
        assert flag == FLAG_VALID

    def test_calculate_cagr_valid_pat(self):
        cagr, flag = calculate_cagr(
            start_value=50, end_value=150, years=3, metric_name="PAT"
        )
        assert cagr == 44.22
        assert flag == FLAG_VALID

    def test_calculate_cagr_valid_eps(self):
        cagr, flag = calculate_cagr(
            start_value=10, end_value=25, years=10, metric_name="EPS"
        )
        assert cagr == 9.60
        assert flag == FLAG_VALID

    def test_cagr_edge_case_zero_base(self):
        cagr, flag = calculate_cagr(start_value=0, end_value=200, years=5)
        assert cagr is None
        assert flag == FLAG_ZERO_BASE

    def test_cagr_edge_case_decline_to_loss(self):
        cagr, flag = calculate_cagr(start_value=100, end_value=-20, years=5)
        assert cagr is None
        assert flag == FLAG_DECLINE_TO_LOSS

        cagr_zero, flag_zero = calculate_cagr(start_value=100, end_value=0, years=5)
        assert cagr_zero is None
        assert flag_zero == FLAG_DECLINE_TO_LOSS

    def test_cagr_edge_case_turnaround(self):
        cagr, flag = calculate_cagr(start_value=-100, end_value=50, years=5)
        assert cagr is None
        assert flag == FLAG_TURNAROUND

    def test_cagr_edge_case_both_negative(self):
        cagr, flag = calculate_cagr(start_value=-50, end_value=-30, years=5)
        assert cagr is None
        assert flag == FLAG_BOTH_NEGATIVE

    def test_cagr_edge_case_insufficient_data(self):
        cagr_yr, flag_yr = calculate_cagr(start_value=100, end_value=150, years=0)
        assert cagr_yr is None
        assert flag_yr == FLAG_INSUFFICIENT

        cagr_none, flag_none = calculate_cagr(start_value=None, end_value=150, years=5)
        assert cagr_none is None
        assert flag_none == FLAG_INSUFFICIENT

    def test_cagr_edge_case_same_value(self):
        cagr, flag = calculate_cagr(start_value=100, end_value=100, years=5)
        assert cagr == 0.0
        assert flag == FLAG_VALID

    def test_cagr_decimal_values(self):
        cagr, flag = calculate_cagr(start_value=100.5, end_value=201.0, years=5)
        assert cagr == 14.87
        assert flag == FLAG_VALID

    def test_cagr_invalid_inputs(self):
        cagr, flag = calculate_cagr(start_value="invalid", end_value=200, years=5)
        assert cagr is None
        assert flag == FLAG_INVALID_INPUT


class TestGrowthClassification:
    def test_growth_classification_tiers(self):
        assert classify_growth_cagr(25.0, FLAG_VALID) == LABEL_HIGH_GROWTH
        assert classify_growth_cagr(15.0, FLAG_VALID) == LABEL_STRONG_GROWTH
        assert classify_growth_cagr(8.0, FLAG_VALID) == LABEL_MODERATE_GROWTH
        assert classify_growth_cagr(3.0, FLAG_VALID) == LABEL_SLOW_GROWTH
        assert classify_growth_cagr(-2.5, FLAG_VALID) == LABEL_DECLINING
        assert classify_growth_cagr(None, FLAG_ZERO_BASE) == LABEL_NOT_APPLICABLE
        assert classify_growth_cagr(15.0, FLAG_TURNAROUND) == LABEL_NOT_APPLICABLE


class TestCAGREngineBatchAndExport:
    def test_cagr_engine_company_batch(self):
        history_data = {
            "year": ["Mar 2014", "Mar 2019", "Mar 2021", "Mar 2024"],
            "sales": [1000.0, 1500.0, 1800.0, 2500.0],
            "net_profit": [100.0, 200.0, 250.0, 400.0],
            "eps": [10.0, 20.0, 25.0, 40.0],
        }
        df_hist = pd.DataFrame(history_data)

        results = CAGREngine.compute_company_cagr("TCS", df_hist)

        # Expect 3 metrics * 3 time windows = 9 results
        assert len(results) == 9

        rev_5y = [
            r for r in results if r.metric_name == "Revenue" and r.period_years == 5
        ][0]
        assert rev_5y.cagr == round(((2500.0 / 1500.0) ** (1 / 5) - 1) * 100, 2)
        assert rev_5y.flag == FLAG_VALID
        assert rev_5y.growth_label == LABEL_STRONG_GROWTH

    def test_cagr_engine_export_reports(self, tmp_path):
        history_data = {
            "year": ["Mar 2014", "Mar 2019", "Mar 2021", "Mar 2024"],
            "sales": [1000.0, 1500.0, 1800.0, 2500.0],
            "net_profit": [100.0, -50.0, 250.0, 400.0],
            "eps": [10.0, 0.0, 25.0, 40.0],
        }
        df_hist = pd.DataFrame(history_data)

        results = CAGREngine.compute_company_cagr("XYZ_LTD", df_hist)
        CAGREngine.export_growth_reports(results, output_dir=tmp_path)

        stats_file = tmp_path / "cagr_statistics.csv"
        summary_file = tmp_path / "growth_summary.csv"

        assert stats_file.exists()
        assert summary_file.exists()

        df_stats = pd.read_csv(stats_file)
        df_summary = pd.read_csv(summary_file)

        assert "Flag" in df_stats.columns
        assert "Count" in df_stats.columns
        assert len(df_summary) == 1
        assert df_summary.iloc[0]["Company"] == "XYZ_LTD"
