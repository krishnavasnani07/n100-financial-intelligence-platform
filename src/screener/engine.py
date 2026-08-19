from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from src.screener.filters import (
    apply_debt_filter,
    apply_interest_filter,
    apply_numeric_filter,
)
from src.screener.utilities import coerce_float

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "config" / "screener_config.yaml"


def load_screener_config(config_path: Path | None = None) -> dict[str, Any]:
    """
    Load screener thresholds from YAML and return them as a dictionary.

    Parameters:
        config_path (Optional[Path]): Path to the YAML config file.

    Returns:
        Dict[str, Any]: Screen configuration dictionary.
    """
    path = config_path or CONFIG_PATH
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    return config if isinstance(config, dict) else {}


def load_financial_ratios_dataframe(
    source: str | Path | pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Load the sprint-2 financial ratios dataset into a DataFrame.

    Parameters:
        source (Optional[Union[str, Path, pd.DataFrame]]): Source file path or existing DataFrame.

    Returns:
        pd.DataFrame: Loaded financial ratios data.
    """
    if isinstance(source, pd.DataFrame):
        return source.copy()

    if source is None:
        source = BASE_DIR / "output" / "financial_ratios.csv"

    if isinstance(source, (str, Path)):
        source_path = Path(source)
        if source_path.exists():
            return pd.read_csv(source_path)

        db_path = BASE_DIR / "db" / "nifty100.db"
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            try:
                return pd.read_sql_query("SELECT * FROM financial_ratios", conn)
            finally:
                conn.close()

    raise FileNotFoundError("Could not locate a financial_ratios dataset to screen")


def filter_companies(
    data: pd.DataFrame | str | Path | None,
    config: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """
    Apply the configured screening rules and return the filtered DataFrame.

    Parameters:
        data (Optional[Union[pd.DataFrame, str, Path]]): Input dataset.
        config (Optional[Dict[str, Any]]): Screener filter config dictionary.

    Returns:
        pd.DataFrame: Sorted, filtered DataFrame of matching companies.
    """
    if data is None:
        return pd.DataFrame()

    frame = load_financial_ratios_dataframe(data)
    thresholds = (
        ((config or {}).get("filters") or {}) if isinstance(config, dict) else {}
    )

    # Only the core identifiers are required; the remaining filters can be resolved from aliases or skipped when absent.
    required_columns = {"sector", "icr_label"}
    missing = required_columns.difference(frame.columns)
    if missing:
        missing_list = sorted(missing)
        raise KeyError(
            f"Input data is missing required screener columns: {missing_list}"
        )

    def _get_threshold(name: str, default: float | None = None) -> float | None:
        raw_value = thresholds.get(name)
        if raw_value is None:
            return default
        return coerce_float(raw_value)

    mask = pd.Series(True, index=frame.index)

    # Apply all numeric filters
    mask = apply_numeric_filter(
        frame, ["return_on_equity_pct", "roe"], _get_threshold("min_roe"), "ge", mask
    )
    mask = apply_debt_filter(frame, _get_threshold("max_debt_to_equity"), mask)
    mask = apply_numeric_filter(
        frame, ["free_cash_flow_cr", "fcf"], _get_threshold("min_fcf"), "ge", mask
    )
    mask = apply_numeric_filter(
        frame,
        ["revenue_cagr_5yr", "rev_cagr_5yr"],
        _get_threshold("min_revenue_cagr_5yr"),
        "ge",
        mask,
    )
    mask = apply_numeric_filter(
        frame,
        ["pat_cagr_5yr", "pat_cagr"],
        _get_threshold("min_pat_cagr_5yr"),
        "ge",
        mask,
    )
    mask = apply_numeric_filter(
        frame,
        ["operating_profit_margin_pct", "opm_pct", "operating_profit_margin"],
        _get_threshold("min_operating_profit_margin"),
        "ge",
        mask,
    )
    mask = apply_numeric_filter(
        frame, ["pe", "price_to_earnings", "p_e"], _get_threshold("max_pe"), "le", mask
    )
    mask = apply_numeric_filter(
        frame, ["pb", "price_to_book", "p_b"], _get_threshold("max_pb"), "le", mask
    )
    mask = apply_numeric_filter(
        frame,
        ["dividend_yield", "dividend_yield_pct", "dividend_payout_ratio_pct"],
        _get_threshold("min_dividend_yield"),
        "ge",
        mask,
    )
    mask = apply_interest_filter(frame, _get_threshold("min_interest_coverage"), mask)
    mask = apply_numeric_filter(
        frame,
        ["market_cap", "market_value"],
        _get_threshold("min_market_cap"),
        "ge",
        mask,
    )
    mask = apply_numeric_filter(
        frame, ["net_profit"], _get_threshold("min_net_profit"), "ge", mask
    )
    mask = apply_numeric_filter(
        frame,
        ["eps_cagr_5yr", "eps_cagr"],
        _get_threshold("min_eps_cagr_5yr"),
        "ge",
        mask,
    )
    mask = apply_numeric_filter(
        frame, ["asset_turnover"], _get_threshold("min_asset_turnover"), "ge", mask
    )
    mask = apply_numeric_filter(
        frame, ["sales", "revenue"], _get_threshold("min_sales"), "ge", mask
    )
    mask = apply_numeric_filter(
        frame,
        ["dividend_payout_ratio_pct", "dividend_payout"],
        _get_threshold("max_dividend_payout"),
        "le",
        mask,
    )
    mask = apply_numeric_filter(
        frame,
        ["revenue_cagr_3yr", "rev_cagr_3yr"],
        _get_threshold("min_revenue_cagr_3yr"),
        "ge",
        mask,
    )

    filtered = frame.loc[mask].copy()
    if "composite_quality_score" in filtered.columns:
        filtered = filtered.sort_values(
            by=["composite_quality_score"], ascending=False, na_position="last"
        ).reset_index(drop=True)
    return filtered
