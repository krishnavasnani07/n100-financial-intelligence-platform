import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.config.settings import DB_PATH, OUTPUT_DIR
from src.peer_analysis.percentile import (
    compute_percentiles,
    calculate_sector_statistics,
)
from src.peer_analysis.benchmark import benchmark_against_sector
from src.peer_analysis.summary import get_top_performers, get_bottom_performers
from src.peer_analysis.comparison import run_peer_analysis


def test_percentile_calculation_higher_is_better():
    """Test percentile ranking where higher values are better (e.g. ROE)."""
    series = pd.Series([10.0, 20.0, 30.0])
    pct = compute_percentiles(series, lower_is_better=False)

    assert pct.iloc[0] == 0.0  # 10.0 is min, gets 0.0 percentile
    assert pct.iloc[1] == 50.0  # 20.0 is median, gets 50.0 percentile
    assert pct.iloc[2] == 100.0  # 30.0 is max, gets 100.0 percentile


def test_percentile_calculation_lower_is_better():
    """Test percentile ranking where lower values are better (e.g. D/E)."""
    series = pd.Series([0.0, 0.5, 2.0])
    pct = compute_percentiles(series, lower_is_better=True)

    assert pct.iloc[0] == 100.0  # 0.0 is best/lowest, gets 100.0 percentile
    assert pct.iloc[1] == 50.0  # 0.5 is median, gets 50.0 percentile
    assert pct.iloc[2] == 0.0  # 2.0 is worst/highest, gets 0.0 percentile


def test_percentile_calculation_ties():
    """Test percentile calculation when there are tied values."""
    series = pd.Series([10.0, 10.0, 20.0])
    pct = compute_percentiles(series, lower_is_better=False)

    assert pct.iloc[0] == 0.0  # Tied min values get 0.0 percentile
    assert pct.iloc[1] == 0.0
    assert pct.iloc[2] == 100.0  # Max value gets 100.0 percentile


def test_percentile_calculation_all_equal():
    """Test percentile calculation when all values are equal."""
    series = pd.Series([15.0, 15.0, 15.0])
    pct = compute_percentiles(series, lower_is_better=False)
    assert (pct == 100.0).all()


def test_percentile_calculation_single_value():
    """Test percentile calculation when there is only one value."""
    series = pd.Series([15.0])
    pct = compute_percentiles(series, lower_is_better=False)
    assert pct.iloc[0] == 100.0


def test_percentile_calculation_missing_values():
    """Test that missing values are handled gracefully (ignored and result in NaN)."""
    series = pd.Series([10.0, np.nan, 20.0])
    pct = compute_percentiles(series, lower_is_better=False)

    assert pct.iloc[0] == 0.0
    assert pd.isna(pct.iloc[1])
    assert pct.iloc[2] == 100.0


def test_sector_statistics():
    """Test calculation of sector statistics."""
    data = pd.DataFrame(
        {
            "Company": ["C1", "C2", "C3", "C4"],
            "Sector": ["IT", "IT", "Banking", "Banking"],
            "ROE": [10.0, 20.0, 15.0, 25.0],
        }
    )

    stats = calculate_sector_statistics(data, ["ROE"])

    # We expect 2 rows (IT, Banking)
    assert len(stats) == 2
    assert set(stats["Sector"]) == {"IT", "Banking"}

    it_stats = stats[stats["Sector"] == "IT"].iloc[0]
    assert it_stats["Mean"] == 15.0
    assert it_stats["Median"] == 15.0
    assert it_stats["Minimum"] == 10.0
    assert it_stats["Maximum"] == 20.0
    assert it_stats["Standard Deviation"] > 0.0


def test_benchmark_against_sector():
    """Test benchmark_against_sector calculations."""
    data = pd.DataFrame(
        {
            "Company": ["C1", "C2", "C3"],
            "Sector": ["IT", "IT", "IT"],
            "ROE": [10.0, 20.0, 30.0],
        }
    )

    benchmarked = benchmark_against_sector(data, ["ROE"])

    # Sector mean is 20.0, sector median is 20.0
    assert benchmarked.loc[0, "ROE_vs_sector_mean"] == -10.0
    assert benchmarked.loc[1, "ROE_vs_sector_mean"] == 0.0
    assert benchmarked.loc[2, "ROE_vs_sector_mean"] == 10.0

    assert benchmarked.loc[0, "ROE_pct_of_sector_median"] == 50.0
    assert benchmarked.loc[1, "ROE_pct_of_sector_median"] == 100.0
    assert benchmarked.loc[2, "ROE_pct_of_sector_median"] == 150.0


def test_top_and_bottom_performers():
    """Test extraction of top and bottom performers per sector."""
    data = pd.DataFrame(
        {
            "Company": ["C1", "C2", "C3", "C4"],
            "Sector": ["IT", "IT", "IT", "IT"],
            "Composite Quality Score": [90.0, 70.0, 80.0, 60.0],
        }
    )

    top = get_top_performers(data, n=2)
    assert len(top) == 2
    assert list(top["Company"]) == ["C1", "C3"]  # 90.0 and 80.0

    bottom = get_bottom_performers(data, n=2)
    assert len(bottom) == 2
    assert set(bottom["Company"]) == {"C2", "C4"}  # 70.0 and 60.0


def test_run_peer_analysis_end_to_end():
    """Test run_peer_analysis execution and output CSV generation."""
    # Execute analysis using the real database
    peer_comp, sector_stats, top_perf, bottom_perf = run_peer_analysis(DB_PATH)

    # 1. Verify returned DataFrames
    assert isinstance(peer_comp, pd.DataFrame)
    assert isinstance(sector_stats, pd.DataFrame)
    assert isinstance(top_perf, pd.DataFrame)
    assert isinstance(bottom_perf, pd.DataFrame)

    assert len(peer_comp) > 0
    assert len(sector_stats) > 0
    assert len(top_perf) > 0
    assert len(bottom_perf) > 0

    # 2. Verify file output existence
    csv_dir = OUTPUT_DIR / "csv"
    assert (csv_dir / "peer_comparison.csv").exists()
    assert (csv_dir / "sector_statistics.csv").exists()
    assert (csv_dir / "top_performers.csv").exists()
    assert (csv_dir / "bottom_performers.csv").exists()

    # 3. Verify columns and value constraints in peer_comparison
    expected_cols = [
        "Company",
        "Sector",
        "Peer Rank",
        "Composite Score",
        "ROE Percentile",
        "ROCE Percentile",
        "Revenue CAGR Percentile",
        "PAT CAGR Percentile",
        "Debt to Equity Percentile",
        "Operating Margin Percentile",
        "Interest Coverage Percentile",
    ]
    for col in expected_cols:
        assert col in peer_comp.columns

    # Check percentile ranges
    percentile_cols = [col for col in peer_comp.columns if "Percentile" in col]
    for col in percentile_cols:
        valid_vals = peer_comp[col].dropna()
        assert (valid_vals >= 0.0).all()
        assert (valid_vals <= 100.0).all()

    # Check peer ranks are unique and sequential within each sector group
    for sector, group in peer_comp.groupby("Sector"):
        ranks = group["Peer Rank"].sort_values()
        assert list(ranks) == list(range(1, len(group) + 1))
