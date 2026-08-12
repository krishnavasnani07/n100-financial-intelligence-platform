"""
Preset Investment Screeners.
Provides 6 predefined analyst screeners and a master runner function.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from src.config.constants import (
    DEBT_FREE_BLUE_CHIP_CRITERIA,
    DIVIDEND_CHAMPION_CRITERIA,
    GROWTH_ACCELERATOR_CRITERIA,
    QUALITY_COMPOUNDER_CRITERIA,
    TURNAROUND_WATCH_CRITERIA,
    VALUE_PICK_CRITERIA,
)
from src.screener.engine import filter_companies


def load_screener_master_data(db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads raw database data, joins sectoral and price information,
    performs dynamic calculations (PE, PB, 3Y CAGR, YoY D/E change),
    calculates sector-relative composite quality scores and ranks,
    and returns the latest year for each company.

    Parameters:
        db_path (Optional[Path]): Path to the SQLite database.

    Returns:
        pd.DataFrame: Loaded and calculated company financial ratio data.
    """
    from src.screener.ranking import calculate_rankings

    df_ranked = calculate_rankings(db_path)
    return df_ranked.sort_values(by="company_id").reset_index(drop=True)


# Preset Screeners


def screen_quality_compounder(data: pd.DataFrame) -> pd.DataFrame:
    """
    Quality Compounder: Find consistently high-quality businesses.
    ROE > 15%, D/E < 1.0, FCF > 0, Revenue CAGR 5yr > 10%

    Parameters:
        data (pd.DataFrame): Financial ratios dataset.

    Returns:
        pd.DataFrame: Screened list of companies.
    """
    return filter_companies(data, QUALITY_COMPOUNDER_CRITERIA)


def screen_value_pick(data: pd.DataFrame) -> pd.DataFrame:
    """
    Value Pick: Find undervalued companies.
    P/E < 20, P/B < 3.0, D/E < 2.0, Dividend Yield > 1%

    Parameters:
        data (pd.DataFrame): Financial ratios dataset.

    Returns:
        pd.DataFrame: Screened list of companies.
    """
    return filter_companies(data, VALUE_PICK_CRITERIA)


def screen_growth_accelerator(data: pd.DataFrame) -> pd.DataFrame:
    """
    Growth Accelerator: Find fast-growing companies.
    PAT CAGR 5yr > 20%, Revenue CAGR 5yr > 15%, D/E < 2.0

    Parameters:
        data (pd.DataFrame): Financial ratios dataset.

    Returns:
        pd.DataFrame: Screened list of companies.
    """
    return filter_companies(data, GROWTH_ACCELERATOR_CRITERIA)


def screen_dividend_champion(data: pd.DataFrame) -> pd.DataFrame:
    """
    Dividend Champion: Mature cash-returning companies.
    Dividend Yield > 2%, Dividend Payout < 80%, FCF > 0

    Parameters:
        data (pd.DataFrame): Financial ratios dataset.

    Returns:
        pd.DataFrame: Screened list of companies.
    """
    return filter_companies(data, DIVIDEND_CHAMPION_CRITERIA)


def screen_debt_free_blue_chip(data: pd.DataFrame) -> pd.DataFrame:
    """
    Debt-Free Blue Chip: Large debt-free companies.
    D/E = 0, ROE > 12%, Revenue (Sales) > 5000 Cr

    Parameters:
        data (pd.DataFrame): Financial ratios dataset.

    Returns:
        pd.DataFrame: Screened list of companies.
    """
    return filter_companies(data, DEBT_FREE_BLUE_CHIP_CRITERIA)


def screen_turnaround_watch(data: pd.DataFrame) -> pd.DataFrame:
    """
    Turnaround Watch: Companies undergoing turnaround.
    Revenue CAGR 3yr > 10%, Latest FCF Positive, Debt (D/E) declining YoY

    Parameters:
        data (pd.DataFrame): Financial ratios dataset.

    Returns:
        pd.DataFrame: Screened list of companies.
    """
    # Filter using engine for FCF and 3Y Revenue CAGR first
    df_filtered = filter_companies(data, TURNAROUND_WATCH_CRITERIA)

    # Filter for Debt declining YoY in memory
    if not df_filtered.empty and "de_declining_yoy" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["de_declining_yoy"]].copy()

    return df_filtered.reset_index(drop=True)


# Master Runner Function


def run_preset(preset_name: str, data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Executes a preset screener by its name and returns the filtered DataFrame.

    Parameters:
        preset_name (str): Name of the preset screener to run.
        data (Optional[pd.DataFrame]): Input master data DataFrame.

    Returns:
        pd.DataFrame: Screened list of companies matching the preset.
    """
    df_source = data if data is not None else load_screener_master_data()

    presets_map = {
        "Quality Compounder": screen_quality_compounder,
        "Value Pick": screen_value_pick,
        "Growth Accelerator": screen_growth_accelerator,
        "Dividend Champion": screen_dividend_champion,
        "Debt-Free Blue Chip": screen_debt_free_blue_chip,
        "Turnaround Watch": screen_turnaround_watch,
    }

    if preset_name not in presets_map:
        raise ValueError(
            f"Unknown preset name: '{preset_name}'. "
            f"Available presets: {list(presets_map.keys())}"
        )

    return presets_map[preset_name](df_source)
