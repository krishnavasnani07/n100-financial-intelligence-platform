"""
Unit tests for the Cash Flow Intelligence & Health Engine.
Verifies CFO Quality, CapEx Intensity, FCF Conversion, Distress, and Deleveraging signals.
"""

import pytest
import pandas as pd
from pathlib import Path

from src.analytics.cashflow_kpis import (
    calculate_cfo_quality,
    classify_cfo_quality,
    calculate_capex_intensity,
    classify_capex_intensity,
    calculate_fcf_conversion,
    run_cashflow_intelligence_pipeline,
)
from src.config.settings import DB_PATH


def test_calculate_cfo_quality():
    """Verify CFO Quality calculation and division by zero/negative PAT handling."""
    # Positive PAT
    assert calculate_cfo_quality(operating_activity=150, net_profit=100) == 1.50
    # Negative/Zero PAT should return None
    assert calculate_cfo_quality(operating_activity=150, net_profit=0) is None
    assert calculate_cfo_quality(operating_activity=150, net_profit=-50) is None
    # None/invalid inputs
    assert calculate_cfo_quality(operating_activity=None, net_profit=100) is None
    assert calculate_cfo_quality(operating_activity=150, net_profit=None) is None


def test_classify_cfo_quality():
    """Verify CFO Quality labeling based on thresholds."""
    assert classify_cfo_quality(1.2) == "High"
    assert classify_cfo_quality(1.0) == "Moderate"
    assert classify_cfo_quality(0.7) == "Moderate"
    assert classify_cfo_quality(0.4) == "Accrual Risk"
    assert classify_cfo_quality(None) is None


def test_calculate_capex_intensity():
    """Verify CapEx Intensity percentage calculation and zero sales handling."""
    # Positive sales
    assert calculate_capex_intensity(investing_activity=-30, sales=1000) == 3.0
    # Zero/negative sales should return None
    assert calculate_capex_intensity(investing_activity=-30, sales=0) is None
    assert calculate_capex_intensity(investing_activity=-30, sales=-100) is None
    # None inputs
    assert calculate_capex_intensity(investing_activity=None, sales=1000) == 0.0
    assert calculate_capex_intensity(investing_activity=-30, sales=None) is None


def test_classify_capex_intensity():
    """Verify CapEx Intensity labeling based on thresholds."""
    assert classify_capex_intensity(2.5) == "Asset Light"
    assert classify_capex_intensity(3.0) == "Moderate"
    assert classify_capex_intensity(6.0) == "Moderate"
    assert classify_capex_intensity(8.0) == "Moderate"
    assert classify_capex_intensity(9.2) == "Capital Intensive"
    assert classify_capex_intensity(None) is None


def test_calculate_fcf_conversion():
    """Verify FCF Conversion calculation and zero operating profit handling."""
    # Positive operating profit
    assert calculate_fcf_conversion(free_cash_flow=200, operating_profit=400) == 50.0
    # Zero/negative operating profit should return None
    assert calculate_fcf_conversion(free_cash_flow=200, operating_profit=0) is None
    assert calculate_fcf_conversion(free_cash_flow=200, operating_profit=-10) is None


def test_pipeline_execution(tmp_path):
    """Verify end-to-end execution of run_cashflow_intelligence_pipeline."""
    # Use real DB, output to tmp_path
    df_intel = run_cashflow_intelligence_pipeline(db_path=DB_PATH, output_dir=tmp_path)

    # Check shape/columns
    assert len(df_intel) == 92
    expected_cols = [
        "company_id",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label",
    ]
    for col in expected_cols:
        assert col in df_intel.columns

    # Check generated files
    assert (tmp_path / "cashflow_intelligence.xlsx").exists()
    assert (tmp_path / "distress_alerts.csv").exists()
