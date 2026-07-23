from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

import sqlite3
import pandas as pd
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "config" / "screener_config.yaml"


def load_screener_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load screener thresholds from YAML and return them as a dictionary."""
    path = config_path or CONFIG_PATH
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    return config if isinstance(config, dict) else {}


def _coerce_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        if isinstance(value, str) and value.strip() == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _get_series(frame: pd.DataFrame, aliases: list[str]) -> Optional[pd.Series]:
    for alias in aliases:
        if alias in frame.columns:
            return frame[alias]
    return None


def load_financial_ratios_dataframe(source: Optional[Union[str, Path, pd.DataFrame]] = None) -> pd.DataFrame:
    """Load the sprint-2 financial ratios dataset into a DataFrame."""
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


def filter_companies(data: Optional[Union[pd.DataFrame, str, Path]], config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """Apply the configured screening rules and return the filtered DataFrame."""
    if data is None:
        return pd.DataFrame()

    frame = load_financial_ratios_dataframe(data)
    thresholds = ((config or {}).get("filters") or {}) if isinstance(config, dict) else {}

    # Only the core identifiers are required; the remaining filters can be resolved from aliases or skipped when absent.
    required_columns = {"sector", "icr_label"}
    missing = required_columns.difference(frame.columns)
    if missing:
        missing_list = sorted(missing)
        raise KeyError(f"Input data is missing required screener columns: {missing_list}")

    def _get_threshold(name: str, default: Optional[float] = None) -> Optional[float]:
        raw_value = thresholds.get(name)
        if raw_value is None:
            return default
        return _coerce_float(raw_value)

    mask = pd.Series(True, index=frame.index)

    def _apply_numeric_filter(column_aliases: list[str], threshold: Optional[float], mode: str = "ge") -> None:
        nonlocal mask
        if threshold is None:
            return
        series = _get_series(frame, column_aliases)
        if series is None:
            return
        values = series.apply(_coerce_float)
        if mode == "ge":
            mask &= values.ge(threshold)
        elif mode == "le":
            mask &= values.le(threshold)
        elif mode == "gt":
            mask &= values.gt(threshold)
        elif mode == "lt":
            mask &= values.lt(threshold)

    min_roe = _get_threshold("min_roe")
    if min_roe is not None:
        _apply_numeric_filter(["return_on_equity_pct", "roe"], min_roe, "ge")

    max_debt_to_equity = _get_threshold("max_debt_to_equity")
    if max_debt_to_equity is not None:
        debt_mask = pd.Series(True, index=frame.index)
        debt_series = _get_series(frame, ["debt_to_equity", "de_ratio", "de_to_equity"])
        for idx, value in frame.iterrows():
            sector = str(value.get("sector", "")).strip().lower()
            if sector == "financials":
                continue
            if debt_series is None:
                continue
            debt_value = _coerce_float(debt_series.iloc[idx])
            if debt_value is not None and debt_value > max_debt_to_equity:
                debt_mask.at[idx] = False
        mask &= debt_mask

    min_fcf = _get_threshold("min_fcf")
    if min_fcf is not None:
        _apply_numeric_filter(["free_cash_flow_cr", "fcf"], min_fcf, "ge")

    min_revenue_cagr_5yr = _get_threshold("min_revenue_cagr_5yr")
    if min_revenue_cagr_5yr is not None:
        _apply_numeric_filter(["revenue_cagr_5yr", "rev_cagr_5yr"], min_revenue_cagr_5yr, "ge")

    min_pat_cagr_5yr = _get_threshold("min_pat_cagr_5yr")
    if min_pat_cagr_5yr is not None:
        _apply_numeric_filter(["pat_cagr_5yr", "pat_cagr"], min_pat_cagr_5yr, "ge")

    min_operating_profit_margin = _get_threshold("min_operating_profit_margin")
    if min_operating_profit_margin is not None:
        _apply_numeric_filter(["operating_profit_margin_pct", "opm_pct", "operating_profit_margin"], min_operating_profit_margin, "ge")

    max_pe = _get_threshold("max_pe")
    if max_pe is not None:
        _apply_numeric_filter(["pe", "price_to_earnings", "p_e"], max_pe, "le")

    max_pb = _get_threshold("max_pb")
    if max_pb is not None:
        _apply_numeric_filter(["pb", "price_to_book", "p_b"], max_pb, "le")

    min_dividend_yield = _get_threshold("min_dividend_yield")
    if min_dividend_yield is not None:
        _apply_numeric_filter(["dividend_yield", "dividend_yield_pct", "dividend_payout_ratio_pct"], min_dividend_yield, "ge")

    min_interest_coverage = _get_threshold("min_interest_coverage")
    if min_interest_coverage is not None:
        interest_mask = pd.Series(True, index=frame.index)
        icr_series = _get_series(frame, ["interest_coverage", "icr", "interest_coverage_ratio"])
        for idx, value in frame.iterrows():
            label = str(value.get("icr_label", "")).strip().lower()
            if label == "debt free":
                continue
            if icr_series is None:
                continue
            icr_value = _coerce_float(icr_series.iloc[idx])
            if icr_value is not None and icr_value < min_interest_coverage:
                interest_mask.at[idx] = False
        mask &= interest_mask

    min_market_cap = _get_threshold("min_market_cap")
    if min_market_cap is not None:
        _apply_numeric_filter(["market_cap", "market_value"], min_market_cap, "ge")

    min_net_profit = _get_threshold("min_net_profit")
    if min_net_profit is not None:
        _apply_numeric_filter(["net_profit"], min_net_profit, "ge")

    min_eps_cagr_5yr = _get_threshold("min_eps_cagr_5yr")
    if min_eps_cagr_5yr is not None:
        _apply_numeric_filter(["eps_cagr_5yr", "eps_cagr"], min_eps_cagr_5yr, "ge")

    min_asset_turnover = _get_threshold("min_asset_turnover")
    if min_asset_turnover is not None:
        _apply_numeric_filter(["asset_turnover"], min_asset_turnover, "ge")

    min_sales = _get_threshold("min_sales")
    if min_sales is not None:
        _apply_numeric_filter(["sales", "revenue"], min_sales, "ge")

    filtered = frame.loc[mask].copy()
    if "composite_quality_score" in filtered.columns:
        filtered = filtered.sort_values(
            by=["composite_quality_score"], ascending=False, na_position="last"
        ).reset_index(drop=True)
    return filtered
