"""
Unit tests for the KMeans Financial Clustering pipeline.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src.analytics.clustering import (
    impute_sector_medians,
    load_clustering_data,
    prepare_features,
    run_kmeans,
    assign_cluster_names,
)
from src.config.settings import DB_PATH


def test_load_clustering_data():
    """
    Verifies that the clustering data is loaded properly from the database.
    """
    df = load_clustering_data(DB_PATH)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 92
    assert "company_id" in df.columns
    assert "sector" in df.columns


def test_impute_sector_medians():
    """
    Verifies sector-median imputation with global fallback.
    """
    # Create test data with missing values
    test_df = pd.DataFrame(
        {
            "company_id": ["C1", "C2", "C3", "C4"],
            "sector": ["IT", "IT", "Finance", "Finance"],
            "return_on_equity_pct": [20.0, None, 15.0, 10.0],
            "debt_to_equity": [
                0.1,
                0.2,
                None,
                None,
            ],  # Finance sector has all NaNs for D/E
            "revenue_cagr_5yr": [12.0, 14.0, 8.0, None],
            "fcf_cagr_5yr": [None, 10.0, 5.0, 6.0],
            "operating_profit_margin_pct": [25.0, 30.0, 18.0, 20.0],
        }
    )

    df_imputed = impute_sector_medians(test_df)

    # 1. C2 ROE (IT) should be imputed with C1's ROE (20.0)
    assert df_imputed.loc[1, "return_on_equity_pct"] == 20.0

    # 2. Finance D/E is all missing, so it should fall back to the global median of IT D/E: median of [0.1, 0.2] = 0.15
    assert df_imputed.loc[2, "debt_to_equity"] == pytest.approx(0.15)
    assert df_imputed.loc[3, "debt_to_equity"] == pytest.approx(0.15)

    # Check no NaNs remain
    for col in [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]:
        assert df_imputed[col].isna().sum() == 0


def test_prepare_features():
    """
    Verifies scaling logic and structure.
    """
    df = load_clustering_data(DB_PATH)
    df_imputed = impute_sector_medians(df)
    X_scaled, scaler = prepare_features(df_imputed)

    assert X_scaled.shape == (92, 5)
    assert isinstance(scaler, StandardScaler)

    # StandardScaler scaled features should have mean close to 0 and std close to 1
    means = X_scaled.mean(axis=0)
    stds = X_scaled.std(axis=0)
    for m, s in zip(means, stds):
        assert abs(m) < 1e-7
        assert abs(s - 1.0) < 1e-7


def test_run_kmeans():
    """
    Verifies KMeans running and distance calculation.
    """
    df = load_clustering_data(DB_PATH)
    df_imputed = impute_sector_medians(df)
    X_scaled, _ = prepare_features(df_imputed)

    cluster_ids, distances, kmeans = run_kmeans(X_scaled)

    assert len(cluster_ids) == 92
    assert len(distances) == 92
    assert isinstance(kmeans, KMeans)
    assert kmeans.n_clusters == 5
    assert set(cluster_ids).issubset(set(range(5)))
    assert all(d >= 0 for d in distances)


def test_assign_cluster_names():
    """
    Verifies dynamic cluster naming.
    """
    df = load_clustering_data(DB_PATH)
    df_imputed = impute_sector_medians(df)
    X_scaled, _ = prepare_features(df_imputed)
    cluster_ids, distances, kmeans = run_kmeans(X_scaled)

    df_imputed["cluster_id"] = cluster_ids
    df_imputed["distance_from_centroid"] = distances

    df_final = assign_cluster_names(df_imputed, kmeans)

    assert "cluster_name" in df_final.columns
    assert df_final["cluster_name"].isna().sum() == 0

    # Check that exact 5 archetypes exist
    unique_names = df_final["cluster_name"].unique()
    assert len(unique_names) == 5

    expected_archetypes = {
        "Highly Leveraged Financials & Utilities",
        "Capital-Efficient Outliers (High ROE)",
        "High-Quality Cash Compounders",
        "Emerging Growth Leaders",
        "Stable Blue Chips & Defensives",
    }
    assert set(unique_names) == expected_archetypes
