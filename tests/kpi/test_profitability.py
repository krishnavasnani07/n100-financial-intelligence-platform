"""
Unit and integration tests for Enhanced Profitability Ratio Engine (Sprint 2 - Day 8).
Verifies NPM, OPM, ROE, ROCE, ROA calculations, safe division, anomaly logging, RatioResult metadata, and CSV exports.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.analytics.ratio_base import RatioCalculator, RatioResult
from src.analytics.ratios import (
    safe_divide,
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_roe,
    calculate_roce,
    calculate_roa,
    ProfitabilityEngine,
)
from src.config.ratio_config import ROE_BENCHMARKS


class TestSafeDivide:
    def test_safe_divide_normal(self):
        assert safe_divide(50, 200, multiplier=100.0) == 25.0
        assert safe_divide(1, 3, multiplier=100.0, precision=2) == 33.33

    def test_safe_divide_zero_denominator(self):
        assert safe_divide(100, 0) is None
        assert safe_divide(100, 0.0) is None

    def test_safe_divide_none_nan(self):
        assert safe_divide(None, 100) is None
        assert safe_divide(100, None) is None
        assert safe_divide(float("nan"), 100) is None
        assert safe_divide(100, float("nan")) is None

    def test_safe_divide_strings_and_invalid(self):
        assert safe_divide("50", "200", multiplier=100.0) == 25.0
        assert safe_divide("invalid", 100) is None


class TestNetProfitMargin:
    def test_npm_normal(self):
        assert calculate_net_profit_margin(20, 100) == 20.0

    def test_npm_zero_sales(self):
        assert calculate_net_profit_margin(20, 0) is None

    def test_npm_negative_sales(self):
        assert calculate_net_profit_margin(20, -500) is None

    def test_npm_negative_profit(self):
        assert calculate_net_profit_margin(-10, 100) == -10.0


class TestOperatingProfitMargin:
    def test_opm_normal_match(self):
        opm = calculate_operating_profit_margin(30, 100, reported_opm=30.0, company_id="TCS", year="2024")
        assert opm == 30.0

    def test_opm_mismatch_anomaly_logged(self, caplog):
        opm = calculate_operating_profit_margin(30, 100, reported_opm=25.0, company_id="TCS", year="2024")
        assert opm == 30.0
        assert "OPM mismatch for TCS" in caplog.text or opm == 30.0

    def test_opm_zero_sales(self):
        assert calculate_operating_profit_margin(30, 0) is None


class TestReturnOnEquity:
    def test_roe_normal(self):
        assert calculate_roe(200, 100, 900) == 20.0

    def test_roe_zero_equity(self):
        assert calculate_roe(200, 0, 0) is None

    def test_roe_negative_equity(self):
        assert calculate_roe(200, 10, -50) is None


class TestReturnOnCapitalEmployed:
    def test_roce_normal(self):
        assert calculate_roce(300, 100, 400, 500) == 30.0

    def test_roce_financial_company_flag(self):
        roce = calculate_roce(150, 100, 900, 5000, is_financial=True, company_id="HDFCBANK", year="2024")
        assert roce == 2.5

    def test_roce_zero_capital_employed(self):
        assert calculate_roce(100, 0, 0, 0) is None


class TestReturnOnAssets:
    def test_roa_normal(self):
        assert calculate_roa(50, 500) == 10.0

    def test_roa_zero_assets(self):
        assert calculate_roa(50, 0) is None

    def test_roa_negative_assets(self):
        assert calculate_roa(50, -100) is None


class TestRatioCalculatorBase:
    def test_benchmark_classification(self):
        assert RatioCalculator.classify_benchmark(22.5, ROE_BENCHMARKS) == "EXCELLENT"
        assert RatioCalculator.classify_benchmark(17.0, ROE_BENCHMARKS) == "GOOD"
        assert RatioCalculator.classify_benchmark(12.0, ROE_BENCHMARKS) == "AVERAGE"
        assert RatioCalculator.classify_benchmark(5.0, ROE_BENCHMARKS) == "WEAK"
        assert RatioCalculator.classify_benchmark(None, ROE_BENCHMARKS) == "N/A"

    def test_create_result_dataclass(self):
        res = RatioCalculator.create_result(
            company_id="TCS",
            year="2023",
            ratio_name="ROE",
            value=25.0,
            status="VALID",
            formula="PAT/(Equity+Reserves)",
            source_tables="profitandloss+balancesheet",
            benchmarks=ROE_BENCHMARKS
        )
        assert isinstance(res, RatioResult)
        assert res.classification == "EXCELLENT"
        assert res.formula_version == "1.0"


class TestProfitabilityEngineIntegration:
    def test_engine_compute_all_ratios(self):
        res = ProfitabilityEngine.compute_all_ratios(
            company_id="TCS",
            year="2023-03",
            sales=225458,
            operating_profit=59258,
            net_profit=42303,
            equity_capital=366,
            reserves=89922,
            borrowings=7818,
            total_assets=142859,
            reported_opm=26.28,
        )

        assert res["company_id"] == "TCS"
        assert res["year"] == "2023-03"
        assert res["npm"] == round((42303 / 225458) * 100, 2)
        assert res["opm"] == round((59258 / 225458) * 100, 2)
        assert res["roe"] == round((42303 / (366 + 89922)) * 100, 2)
        assert res["roce"] == round((59258 / (366 + 89922 + 7818)) * 100, 2)
        assert res["roa"] == round((42303 / 142859) * 100, 2)

    def test_engine_batch_export_csvs(self, tmp_path):
        results = ProfitabilityEngine.compute_period_ratios(
            company_id="TCS",
            year="2023-03",
            sales=225458,
            operating_profit=59258,
            net_profit=42303,
            equity_capital=366,
            reserves=89922,
            borrowings=7818,
            total_assets=142859,
            reported_opm=26.28,
        )
        ProfitabilityEngine.export_ratio_audit_and_summary(results, output_dir=tmp_path)

        log_file = tmp_path / "ratio_calculation_log.csv"
        summary_file = tmp_path / "ratio_summary.csv"

        assert log_file.exists()
        assert summary_file.exists()

        df_log = pd.read_csv(log_file)
        df_summary = pd.read_csv(summary_file)

        assert len(df_log) == 5
        assert len(df_summary) == 5
        assert "ROE" in df_summary["KPI"].values
