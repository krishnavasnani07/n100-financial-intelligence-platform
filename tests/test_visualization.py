"""
Unit and Integration Tests for Visualizations.
"""

from __future__ import annotations
import pytest
from pathlib import Path
from src.config.settings import DB_PATH, OUTPUT_DIR
from src.visualization.radar_chart import generate_single_radar, generate_peer_radar, load_universe_data, calculate_normalized_metrics
from src.visualization.charts import generate_trend_charts
from src.visualization.heatmaps import generate_sector_heatmap
from src.visualization.export import export_all_charts


def test_load_universe_data():
    """Test loading data from the database and check columns."""
    df = load_universe_data()
    assert not df.empty
    assert "company_id" in df.columns
    assert "current_ratio" in df.columns
    assert "roe" in df.columns


def test_calculate_normalized_metrics():
    """Test that metrics are properly normalized between 0 and 100."""
    df_raw = load_universe_data()
    df_norm = calculate_normalized_metrics(df_raw)
    
    assert not df_norm.empty
    for col in ["roe", "roce", "revenue_cagr", "pat_cagr", "operating_margin", "current_ratio", "debt_to_equity", "composite_score"]:
        assert col in df_norm.columns
        # Norm scores should be bounded by [0, 100]
        valid_vals = df_norm[col].dropna()
        assert (valid_vals >= 0.0).all()
        assert (valid_vals <= 100.0).all()


def test_generate_single_radar(tmp_path):
    """Test generating a single company radar chart."""
    save_path = tmp_path / "TCS_radar.png"
    result_path = generate_single_radar("TCS", save_path=save_path)
    
    assert result_path.exists()
    assert result_path.stat().st_size > 0


def test_generate_peer_radar(tmp_path):
    """Test generating peer overlay radar chart."""
    save_path = tmp_path / "INFY_vs_TCS_radar.png"
    result_path = generate_peer_radar("INFY", "TCS", save_path=save_path)
    
    assert result_path.exists()
    assert result_path.stat().st_size > 0


def test_generate_trend_charts(tmp_path):
    """Test historical trend line plot creation."""
    save_path = tmp_path / "INFY_trends.png"
    result_path = generate_trend_charts("INFY", save_path=save_path)
    
    assert result_path.exists()
    assert result_path.stat().st_size > 0


def test_generate_sector_heatmap(tmp_path):
    """Test generating sector heatmap."""
    save_path = tmp_path / "it_heatmap.png"
    result_path = generate_sector_heatmap("Information Technology", save_path=save_path)
    
    assert result_path.exists()
    assert result_path.stat().st_size > 0


def test_generate_sector_heatmap_invalid_sector():
    """Test that invalid sector name raises ValueError."""
    with pytest.raises(ValueError, match="No data found for sector"):
        generate_sector_heatmap("Non-Existent Sector")


def test_export_all_charts(tmp_path):
    """Test bulk export runs without errors and initializes directories."""
    # Run bulk export utilizing the tmp_path as target directory
    export_all_charts(output_dir=tmp_path)
    
    radar_dir = tmp_path / "charts" / "radar"
    peer_dir = tmp_path / "charts" / "peer"
    trend_dir = tmp_path / "charts" / "trends"
    heatmap_dir = tmp_path / "charts" / "heatmaps"
    
    assert radar_dir.exists()
    assert peer_dir.exists()
    assert trend_dir.exists()
    assert heatmap_dir.exists()
