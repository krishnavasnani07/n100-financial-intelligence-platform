"""
Unit and integration tests for Leverage & Efficiency Ratio Engine (Sprint 2 - Day 9).
Verifies D/E, ICR, Net Debt, Asset Turnover, High Leverage Flag, ICR Warning, Debt Free label, and CSV exports.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.analytics.ratio_base import RatioCalculator, RatioResult
from src.analytics.ratios import (
    calculate_debt_to_equity,
    calculate_high_leverage_flag,
    calculate_interest_coverage,
    calculate_icr_warning,
    calculate_icr_label,
    calculate_net_debt,
    calculate_asset_turnover,
    LeverageEngine,
)


class TestDebtToEquity:
    def test_de_normal(self):
        # Borrowings = 500, Equity = 100, Reserves = 900 -> 500 / 1000 = 0.5
        assert calculate_debt_to_equity(500, 100, 900) == 0.5

    def test_de_zero_borrowings(self):
        # Borrowings = 0 -> Returns 0.0, NOT None
        assert calculate_debt_to_equity(0, 100, 900) == 0.0

    def test_de_negative_equity(self):
        # Equity + Reserves <= 0 -> Returns None
        assert calculate_debt_to_equity(500, 10, -50) is None
        assert calculate_debt_to_equity(0, 0, 0) is None

    def test_high_leverage_flag(self):
        # D/E > 5.0 -> True for non-financials
        assert calculate_high_leverage_flag(6.8, is_financial=False) is True
        assert calculate_high_leverage_flag(2.0, is_financial=False) is False

    def test_financial_company_exemption(self):
        # Financial companies exempt from high leverage flag
        assert calculate_high_leverage_flag(6.8, is_financial=True) is False


class TestInterestCoverageRatio:
    def test_icr_normal(self):
        # Op Profit = 100, Other Income = 20, Interest = 30 -> (100 + 20) / 30 = 4.0
        assert calculate_interest_coverage(100, 30, other_income=20) == 4.0

    def test_icr_zero_interest(self):
        # Interest = 0 -> Returns None
        assert calculate_interest_coverage(100, 0, other_income=20) is None

    def test_debt_free_label(self):
        assert calculate_icr_label(interest=0) == "Debt Free"
        assert calculate_icr_label(interest=50, icr_ratio=6.0) == "Strong"
        assert calculate_icr_label(interest=50, icr_ratio=3.0) == "Healthy"
        assert calculate_icr_label(interest=50, icr_ratio=1.7) == "Watch"
        assert calculate_icr_label(interest=50, icr_ratio=1.2) == "Risky"

    def test_icr_warning_flag(self):
        # ICR < 1.5 -> True
        assert calculate_icr_warning(1.2) is True
        assert calculate_icr_warning(1.5) is False
        assert calculate_icr_warning(4.0) is False
        assert calculate_icr_warning(None) is False


class TestNetDebt:
    def test_net_debt_positive(self):
        # Borrowings = 1000, Investments = 300 -> 700
        assert calculate_net_debt(1000, 300) == 700.0

    def test_net_debt_negative(self):
        # Borrowings = 200, Investments = 500 -> -300 (Cash-rich company)
        assert calculate_net_debt(200, 500) == -300.0


class TestAssetTurnover:
    def test_asset_turnover_normal(self):
        # Sales = 1200, Total Assets = 800 -> 1.5
        assert calculate_asset_turnover(1200, 800) == 1.5

    def test_asset_turnover_zero_assets(self):
        assert calculate_asset_turnover(1200, 0) is None

    def test_asset_turnover_negative_assets(self):
        assert calculate_asset_turnover(1200, -500) is None


class TestLeverageEngineIntegration:
    def test_engine_manufacturing_company(self):
        # Tata Steel / Manufacturing example
        res = LeverageEngine.compute_all_ratios(
            company_id="TATASTEEL",
            year="2024",
            borrowings=85000,
            equity_capital=1200,
            reserves=98000,
            operating_profit=25000,
            interest=6000,
            investments=12000,
            sales=230000,
            total_assets=280000,
            other_income=1500,
            is_financial=False,
        )

        assert res["company_id"] == "TATASTEEL"
        assert res["d/e"] == round(85000 / (1200 + 98000), 2)
        assert res["icr"] == round((25000 + 1500) / 6000, 2)
        assert res["net_debt"] == 85000 - 12000
        assert res["asset_turnover"] == round(230000 / 280000, 2)
        assert res["high_leverage_flag"] is False
        assert res["icr_warning"] is False
        assert res["icr_label"] == "Healthy"

    def test_engine_it_debt_free(self):
        # TCS / IT example (Debt Free)
        res = LeverageEngine.compute_all_ratios(
            company_id="TCS",
            year="2024",
            borrowings=0,
            equity_capital=366,
            reserves=89922,
            operating_profit=59258,
            interest=0,
            investments=45000,
            sales=225458,
            total_assets=142859,
            other_income=3000,
            is_financial=False,
        )

        assert res["d/e"] == 0.0
        assert res["icr"] is None
        assert res["net_debt"] == -45000.0
        assert res["high_leverage_flag"] is False
        assert res["icr_label"] == "Debt Free"

    def test_engine_banking_sector(self):
        # HDFC Bank / Financial entity
        res = LeverageEngine.compute_all_ratios(
            company_id="HDFCBANK",
            year="2024",
            borrowings=600000,
            equity_capital=750,
            reserves=90000,
            operating_profit=70000,
            interest=35000,
            investments=150000,
            sales=120000,
            total_assets=2500000,
            other_income=10000,
            is_financial=True,
        )

        # High leverage flag should be False because is_financial=True
        assert res["high_leverage_flag"] is False

    def test_engine_batch_export_csvs(self, tmp_path):
        results = LeverageEngine.compute_period_ratios(
            company_id="TCS",
            year="2024",
            borrowings=0,
            equity_capital=366,
            reserves=89922,
            operating_profit=59258,
            interest=0,
            investments=45000,
            sales=225458,
            total_assets=142859,
            other_income=3000,
            is_financial=False,
        )
        LeverageEngine.export_ratio_audit_and_summary(results, output_dir=tmp_path)

        log_file = tmp_path / "leverage_ratio_calculation_log.csv"
        summary_file = tmp_path / "leverage_ratio_summary.csv"

        assert log_file.exists()
        assert summary_file.exists()

        df_log = pd.read_csv(log_file)
        df_summary = pd.read_csv(summary_file)

        assert len(df_log) == 4
        assert len(df_summary) == 4
        assert "D/E" in df_summary["KPI"].values
