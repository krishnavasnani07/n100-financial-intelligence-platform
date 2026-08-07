import pandas as pd
import pytest

from src.config.settings import DB_PATH
from src.screener.presets import load_screener_master_data, run_preset
from src.utils.helpers import map_year_to_price_date


def test_map_year_to_price_date():
    """Test date mapping function for various month-year inputs."""
    assert map_year_to_price_date("Mar 2024") == "2024-03-01"
    assert map_year_to_price_date("Dec 2012") == "2012-12-01"
    assert map_year_to_price_date("Jan 2020") == "2020-01-01"
    assert map_year_to_price_date("TTM") is None
    assert map_year_to_price_date(None) is None


def test_load_screener_master_data():
    """Test loading and enrichment of the screening master dataframe."""
    df = load_screener_master_data(DB_PATH)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0

    # Check expected columns
    expected_cols = [
        "company_id",
        "year",
        "sector",
        "sales",
        "interest",
        "pe",
        "pb",
        "icr_label",
        "de_declining_yoy",
        "revenue_cagr_3yr",
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing column: {col}"


def test_run_preset_success():
    """Test that all 6 presets can be executed by run_preset."""
    presets = [
        "Quality Compounder",
        "Value Pick",
        "Growth Accelerator",
        "Dividend Champion",
        "Debt-Free Blue Chip",
        "Turnaround Watch",
    ]

    # Load data once to speed up tests
    master_df = load_screener_master_data(DB_PATH)

    for name in presets:
        df_res = run_preset(name, master_df)
        assert isinstance(
            df_res, pd.DataFrame
        ), f"Preset {name} did not return a DataFrame"

        # Verify that companies returned are unique
        assert df_res[
            "company_id"
        ].is_unique, f"Preset {name} returned duplicate companies"


def test_run_preset_invalid_name():
    """Test that run_preset raises ValueError on unknown preset name."""
    with pytest.raises(ValueError, match="Unknown preset name"):
        run_preset("NonExistentPreset")
