"""
Unit and integration tests for Cash Flow Analytics Engine & Capital Allocation Classifier (Sprint 2 - Day 11).
Verifies FCF, CFO Quality, CapEx Intensity, FCF Conversion, 8 Capital Allocation Patterns, and Report Exports.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.analytics.cashflow_kpis import (
    safe_divide,
    get_sign,
    average_last_n_years,
    classify_cfo_quality,
    classify_capex_intensity,
    calculate_free_cash_flow,
    calculate_cfo_quality,
    calculate_capex_intensity,
    calculate_fcf_conversion,
    classify_capital_allocation,
    CashFlowEngine,
)


class TestFreeCashFlow:
    def test_fcf_positive(self):
        # CFO = 500, CFI = -120 -> 380
        assert calculate_free_cash_flow(500, -120) == 380.0

    def test_fcf_negative(self):
        # CFO = 100, CFI = -300 -> -200 (Valid negative FCF)
        assert calculate_free_cash_flow(100, -300) == -200.0

    def test_fcf_zero(self):
        assert calculate_free_cash_flow(150, -150) == 0.0

    def test_fcf_invalid_inputs(self):
        assert calculate_free_cash_flow(None, None) == 0.0


class TestCFOQuality:
    def test_cfo_quality_high(self):
        # CFO = 1200, PAT = 1000 -> Ratio 1.2 (>1.0 High)
        ratio = calculate_cfo_quality(1200, 1000)
        assert ratio == 1.2
        assert classify_cfo_quality(ratio) == "High"

    def test_cfo_quality_moderate(self):
        # CFO = 800, PAT = 1000 -> Ratio 0.8 (0.5–1.0 Moderate)
        ratio = calculate_cfo_quality(800, 1000)
        assert ratio == 0.8
        assert classify_cfo_quality(ratio) == "Moderate"

    def test_cfo_quality_accrual_risk(self):
        # CFO = 400, PAT = 1000 -> Ratio 0.4 (<0.5 Accrual Risk)
        ratio = calculate_cfo_quality(400, 1000)
        assert ratio == 0.4
        assert classify_cfo_quality(ratio) == "Accrual Risk"

    def test_cfo_quality_zero_pat(self):
        # PAT = 0 -> Returns None
        assert calculate_cfo_quality(500, 0) is None

    def test_cfo_quality_negative_pat(self):
        # PAT < 0 -> Returns None (Skipped with log warning)
        assert calculate_cfo_quality(500, -100) is None

    def test_cfo_quality_5yr_average(self):
        vals = [1.2, 1.1, 0.9, 1.3, 1.0]
        avg = average_last_n_years(vals, n=5)
        assert avg == 1.1


class TestCapExIntensity:
    def test_capex_asset_light(self):
        # CFI = -20, Sales = 1000 -> ABS(-20)/1000 * 100 = 2.0% (<3% Asset Light)
        pct = calculate_capex_intensity(-20, 1000)
        assert pct == 2.0
        assert classify_capex_intensity(pct) == "Asset Light"

    def test_capex_moderate(self):
        # CFI = -50, Sales = 1000 -> 5.0% (3-8% Moderate)
        pct = calculate_capex_intensity(-50, 1000)
        assert pct == 5.0
        assert classify_capex_intensity(pct) == "Moderate"

    def test_capex_capital_intensive(self):
        # CFI = -120, Sales = 1000 -> 12.0% (>8% Capital Intensive)
        pct = calculate_capex_intensity(-120, 1000)
        assert pct == 12.0
        assert classify_capex_intensity(pct) == "Capital Intensive"

    def test_capex_zero_sales(self):
        assert calculate_capex_intensity(-50, 0) is None
        assert calculate_capex_intensity(-50, -100) is None


class TestFCFConversion:
    def test_fcf_conversion_normal(self):
        # FCF = 400, Operating Profit = 500 -> 80.0%
        assert calculate_fcf_conversion(400, 500) == 80.0

    def test_fcf_conversion_zero_op(self):
        assert calculate_fcf_conversion(400, 0) is None
        assert calculate_fcf_conversion(400, -100) is None


class TestCapitalAllocationClassifier:
    def test_reinvestor(self):
        # CFO (+), CFI (-), CFF (-) with normal/low CFO/PAT
        cfo_s, cfi_s, cff_s, label = classify_capital_allocation(500, -200, -100, cfo_pat_ratio=0.9)
        assert (cfo_s, cfi_s, cff_s) == ("+", "-", "-")
        assert label == "Reinvestor"

    def test_shareholder_returns(self):
        # CFO (+), CFI (-), CFF (-) with high CFO/PAT (>1.0)
        cfo_s, cfi_s, cff_s, label = classify_capital_allocation(500, -100, -300, cfo_pat_ratio=1.2)
        assert (cfo_s, cfi_s, cff_s) == ("+", "-", "-")
        assert label == "Shareholder Returns"

    def test_liquidating_assets(self):
        # CFO (+), CFI (+), CFF (-)
        _, _, _, label = classify_capital_allocation(300, 100, -150)
        assert label == "Liquidating Assets"

    def test_distress_signal(self):
        # CFO (-), CFI (+), CFF (+)
        _, _, _, label = classify_capital_allocation(-100, 50, 80)
        assert label == "Distress Signal"

    def test_growth_funded_by_debt(self):
        # CFO (-), CFI (-), CFF (+)
        _, _, _, label = classify_capital_allocation(-50, -200, 300)
        assert label == "Growth Funded by Debt"

    def test_cash_accumulator(self):
        # CFO (+), CFI (+), CFF (+)
        _, _, _, label = classify_capital_allocation(200, 50, 100)
        assert label == "Cash Accumulator"

    def test_pre_revenue(self):
        # CFO (-), CFI (-), CFF (-)
        _, _, _, label = classify_capital_allocation(-50, -30, -20)
        assert label == "Pre-Revenue"

    def test_mixed(self):
        # CFO (+), CFI (-), CFF (+)
        _, _, _, label = classify_capital_allocation(300, -100, 50)
        assert label == "Mixed"


class TestCashFlowEngineIntegration:
    def test_engine_company_kpis_calculation(self):
        # TCS multi-year mock data
        data = [
            {"company_id": "TCS", "year": "2020", "operating_activity": 35000, "investing_activity": -8000, "financing_activity": -25000, "sales": 156000, "operating_profit": 42000, "net_profit": 32000},
            {"company_id": "TCS", "year": "2021", "operating_activity": 38000, "investing_activity": -7000, "financing_activity": -28000, "sales": 164000, "operating_profit": 46000, "net_profit": 35000},
            {"company_id": "TCS", "year": "2022", "operating_activity": 39000, "investing_activity": -6000, "financing_activity": -30000, "sales": 191000, "operating_profit": 53000, "net_profit": 38000},
            {"company_id": "TCS", "year": "2023", "operating_activity": 42000, "investing_activity": -5000, "financing_activity": -35000, "sales": 225000, "operating_profit": 59000, "net_profit": 42000},
            {"company_id": "TCS", "year": "2024", "operating_activity": 45000, "investing_activity": -4000, "financing_activity": -38000, "sales": 240000, "operating_profit": 64000, "net_profit": 46000},
        ]
        df_tcs = pd.DataFrame(data)

        results = CashFlowEngine.compute_company_cashflow_kpis("TCS", df_tcs)
        assert len(results) == 5

        res_2024 = results[-1]
        assert res_2024["company_id"] == "TCS"
        assert res_2024["year"] == "2024"
        assert res_2024["free_cash_flow"] == 41000.0  # 45000 - 4000
        assert res_2024["capex_intensity_label"] == "Asset Light"
        assert res_2024["pattern_label"] == "Shareholder Returns"

    def test_engine_export_reports(self, tmp_path):
        results = [
            {
                "company_id": "INFY", "year": "2024", "free_cash_flow": 22000.0,
                "cfo_quality_period": 1.05, "cfo_quality_5yr_avg": 1.02, "cfo_quality_label": "High",
                "capex_intensity_pct": 2.5, "capex_intensity_label": "Asset Light",
                "fcf_conversion": 0.85, "cfo_sign": "+", "cfi_sign": "-", "cff_sign": "-",
                "pattern_label": "Shareholder Returns"
            },
            {
                "company_id": "RELIANCE", "year": "2024", "free_cash_flow": 15000.0,
                "cfo_quality_period": 0.9, "cfo_quality_5yr_avg": 0.88, "cfo_quality_label": "Moderate",
                "capex_intensity_pct": 11.2, "capex_intensity_label": "Capital Intensive",
                "fcf_conversion": 0.45, "cfo_sign": "+", "cfi_sign": "-", "cff_sign": "+",
                "pattern_label": "Mixed"
            }
        ]

        files = CashFlowEngine.export_cashflow_reports(results, output_dir=tmp_path)

        assert files["capital_allocation"].exists()
        assert files["cashflow_summary"].exists()
        assert files["pattern_statistics"].exists()

        df_alloc = pd.read_csv(files["capital_allocation"])
        df_stats = pd.read_csv(files["pattern_statistics"])

        assert len(df_alloc) == 2
        assert "pattern_label" in df_alloc.columns
        assert "pattern_label" in df_stats.columns
        assert len(df_stats) == 2
