"""
Unit tests for S6 Day 37 cluster profiling and portfolio intelligence.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from src.analytics.cluster_profile import (detect_sector_outliers, generate_portfolio_stats,
                                           impute_clustering_features, load_cluster_data,
                                           profile_clusters)
from src.config.settings import DB_PATH, OUTPUT_DIR


def test_load_cluster_data():
    """
    Verifies merged data length and columns.
    """
    df = load_cluster_data(DB_PATH)
    assert len(df) == 92
    assert "cluster_id" in df.columns
    assert "cluster_name" in df.columns
    assert "distance_from_centroid" in df.columns


def test_profile_clusters():
    """
    Verifies cluster profile mean/median stats and file creation.
    """
    df = load_cluster_data(DB_PATH)
    df_imputed = impute_clustering_features(df)
    profiles_df = profile_clusters(df_imputed)
    
    assert isinstance(profiles_df, pd.DataFrame)
    assert len(profiles_df) == 5
    assert "company_count" in profiles_df.columns
    assert profiles_df["company_count"].sum() == 92
    
    # Check output file exists
    out_file = OUTPUT_DIR / "cluster_profiles.csv"
    assert out_file.exists()
    
    # Check that columns are populated and non-empty
    df_saved = pd.read_csv(out_file)
    assert len(df_saved) == 5
    assert "roe_mean" in df_saved.columns
    assert "roe_median" in df_saved.columns


def test_detect_sector_outliers_zero_variance():
    """
    Verifies outlier detection handles standard deviation of zero without crashing.
    """
    # Create test data with single company in a sector (variance is NaN/0)
    test_df = pd.DataFrame({
        "company_id": ["C1", "C2", "C3"],
        "company_name": ["C1 Name", "C2 Name", "C3 Name"],
        "sector": ["IT", "IT", "OnlyOne"],  # OnlyOne sector has 1 company
        "return_on_equity_pct": [20.0, 20.0, 15.0],  # IT has 0 variance, OnlyOne has 1 element
        "return_on_capital_employed_pct": [22.0, 24.0, 18.0],
        "net_profit_margin_pct": [15.0, 16.0, 12.0],
        "debt_to_equity": [0.1, 0.2, 0.3],
        "free_cash_flow_cr": [10.0, 20.0, 30.0],
        "pat_cagr_5yr": [10.0, 12.0, 14.0],
        "revenue_cagr_5yr": [8.0, 9.0, 10.0],
        "eps_cagr_5yr": [7.0, 8.0, 9.0],
        "interest_coverage": [15.0, 16.0, 17.0],
        "asset_turnover": [1.1, 1.2, 1.3]
    })
    
    outliers = detect_sector_outliers(test_df)
    # Should run successfully without ZeroDivisionError and return empty or normal outliers
    assert isinstance(outliers, pd.DataFrame)
    if not outliers.empty:
        # None of them should have Z > 3 because small sample size or 0 variance doesn't produce Z > 3 in our logic
        assert all(abs(outliers["z_score"]) > 3)


def test_detect_sector_outliers_real_data():
    """
    Verifies sector outlier detection generates outlier_report.csv and has correct columns.
    """
    df = load_cluster_data(DB_PATH)
    outliers = detect_sector_outliers(df)
    
    assert isinstance(outliers, pd.DataFrame)
    out_file = OUTPUT_DIR / "outlier_report.csv"
    assert out_file.exists()
    
    df_saved = pd.read_csv(out_file)
    assert "company_id" in df_saved.columns
    assert "metric" in df_saved.columns
    assert "z_score" in df_saved.columns
    
    # Z-scores of flagged outliers must be greater than 3 in absolute value
    assert (df_saved["z_score"].abs() > 3).all()


def test_generate_portfolio_stats():
    """
    Verifies portfolio percentile bounds and formatting.
    """
    df = load_cluster_data(DB_PATH)
    stats_df = generate_portfolio_stats(df)
    
    assert isinstance(stats_df, pd.DataFrame)
    assert len(stats_df) == 10  # 10 KPIs
    
    out_file = OUTPUT_DIR / "portfolio_stats.csv"
    assert out_file.exists()
    
    df_saved = pd.read_csv(out_file)
    assert len(df_saved) == 10
    
    # Verify P10 <= P25 <= P50 <= P75 <= P90 for all metrics
    for _, row in df_saved.iterrows():
        assert row["p10"] <= row["p25"]
        assert row["p25"] <= row["p50"]
        assert row["p50"] <= row["p75"]
        assert row["p75"] <= row["p90"]
        assert not pd.isnull(row["mean"])
        assert not pd.isnull(row["std"])
