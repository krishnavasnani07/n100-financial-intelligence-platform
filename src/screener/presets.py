"""
Preset Investment Screeners.
Provides 6 predefined analyst screeners and a master runner function.
"""

from __future__ import annotations

import re
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Union

from src.config.settings import DB_PATH, BASE_DIR
from src.analytics.ratios import calculate_icr_label
from src.analytics.cagr import calculate_cagr
from src.screener.engine import filter_companies


def map_year_to_price_date(year_str: str) -> Optional[str]:
    """
    Maps financial year strings to stock price date strings.
    E.g. "Mar 2024" -> "2024-03-01", "Dec 2012" -> "2012-12-01".
    """
    if not year_str:
        return None
    months = {
        "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
        "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
    }
    match = re.search(r"\b([A-Za-z]{3})\s+(\d{4})\b", str(year_str).strip())
    if match:
        m = match.group(1).upper()
        y = match.group(2)
        m_num = months.get(m)
        if m_num:
            return f"{y}-{m_num}-01"
    return None


def extract_year_int(yr_val: Any) -> Optional[int]:
    """Extract 4-digit calendar year integer from year string, returning None for TTM/invalid."""
    if str(yr_val).strip().upper() == "TTM":
        return None
    m = re.search(r"\b(19\d\d|20\d\d)\b", str(yr_val))
    return int(m.group(1)) if m else None


def load_screener_master_data(db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads raw database data, joins sectoral and price information,
    performs dynamic calculations (PE, PB, 3Y CAGR, YoY D/E change),
    calculates sector-relative composite quality scores and ranks,
    and returns the latest year for each company.
    """
    from src.screener.ranking import calculate_rankings
    df_ranked = calculate_rankings(db_path)
    return df_ranked.sort_values(by="company_id").reset_index(drop=True)


# Preset Screeners

def screen_quality_compounder(data: pd.DataFrame) -> pd.DataFrame:
    """
    Quality Compounder: Find consistently high-quality businesses.
    ROE > 15%, D/E < 1.0, FCF > 0, Revenue CAGR 5yr > 10%
    """
    config = {
        "filters": {
            "min_roe": 15.0,
            "max_debt_to_equity": 1.0,
            "min_fcf": 0.0,
            "min_revenue_cagr_5yr": 10.0
        }
    }
    return filter_companies(data, config)


def screen_value_pick(data: pd.DataFrame) -> pd.DataFrame:
    """
    Value Pick: Find undervalued companies.
    P/E < 20, P/B < 3.0, D/E < 2.0, Dividend Yield > 1%
    """
    config = {
        "filters": {
            "max_pe": 20.0,
            "max_pb": 3.0,
            "max_debt_to_equity": 2.0,
            "min_dividend_yield": 1.0
        }
    }
    return filter_companies(data, config)


def screen_growth_accelerator(data: pd.DataFrame) -> pd.DataFrame:
    """
    Growth Accelerator: Find fast-growing companies.
    PAT CAGR 5yr > 20%, Revenue CAGR 5yr > 15%, D/E < 2.0
    """
    config = {
        "filters": {
            "min_pat_cagr_5yr": 20.0,
            "min_revenue_cagr_5yr": 15.0,
            "max_debt_to_equity": 2.0
        }
    }
    return filter_companies(data, config)


def screen_dividend_champion(data: pd.DataFrame) -> pd.DataFrame:
    """
    Dividend Champion: Mature cash-returning companies.
    Dividend Yield > 2% (mapped to min_dividend_yield), Dividend Payout < 80%, FCF > 0
    """
    config = {
        "filters": {
            "min_dividend_yield": 2.0,
            "max_dividend_payout": 80.0,
            "min_fcf": 0.0
        }
    }
    return filter_companies(data, config)


def screen_debt_free_blue_chip(data: pd.DataFrame) -> pd.DataFrame:
    """
    Debt-Free Blue Chip: Large debt-free companies.
    D/E = 0, ROE > 12%, Revenue (Sales) > 5000 Cr
    """
    config = {
        "filters": {
            "max_debt_to_equity": 0.0,
            "min_roe": 12.0,
            "min_sales": 5000.0
        }
    }
    return filter_companies(data, config)


def screen_turnaround_watch(data: pd.DataFrame) -> pd.DataFrame:
    """
    Turnaround Watch: Companies undergoing turnaround.
    Revenue CAGR 3yr > 10%, Latest FCF Positive, Debt (D/E) declining YoY
    """
    config = {
        "filters": {
            "min_fcf": 0.0,
            "min_revenue_cagr_3yr": 10.0
        }
    }
    # Filter using engine for FCF and 3Y Revenue CAGR first
    df_filtered = filter_companies(data, config)
    
    # Filter for Debt declining YoY in memory
    if not df_filtered.empty and "de_declining_yoy" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["de_declining_yoy"] == True].copy()
        
    return df_filtered.reset_index(drop=True)


# Master Runner Function

def run_preset(preset_name: str, data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Executes a preset screener by its name and returns the filtered DataFrame.
    """
    df_source = data if data is not None else load_screener_master_data()
    
    presets_map = {
        "Quality Compounder": screen_quality_compounder,
        "Value Pick": screen_value_pick,
        "Growth Accelerator": screen_growth_accelerator,
        "Dividend Champion": screen_dividend_champion,
        "Debt-Free Blue Chip": screen_debt_free_blue_chip,
        "Turnaround Watch": screen_turnaround_watch
    }
    
    if preset_name not in presets_map:
        raise ValueError(
            f"Unknown preset name: '{preset_name}'. "
            f"Available presets: {list(presets_map.keys())}"
        )
        
    return presets_map[preset_name](df_source)
