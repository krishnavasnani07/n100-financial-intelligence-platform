"""
Filtering functions for the Screener Engine.
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from src.screener.utilities import coerce_float, get_series


def apply_numeric_filter(
    frame: pd.DataFrame,
    column_aliases: list[str],
    threshold: Optional[float],
    mode: str,
    mask: pd.Series,
) -> pd.Series:
    """Applies a numeric filter (ge, le, gt, lt) using a column alias list to update a boolean mask."""
    if threshold is None:
        return mask
    series = get_series(frame, column_aliases)
    if series is None:
        return mask
    values = series.apply(coerce_float)
    if mode == "ge":
        mask = mask & values.ge(threshold)
    elif mode == "le":
        mask = mask & values.le(threshold)
    elif mode == "gt":
        mask = mask & values.gt(threshold)
    elif mode == "lt":
        mask = mask & values.lt(threshold)
    return mask


def apply_debt_filter(
    frame: pd.DataFrame, max_debt_to_equity: Optional[float], mask: pd.Series
) -> pd.Series:
    """Applies a sector-aware debt-to-equity filter, skipping the Financials sector."""
    if max_debt_to_equity is None:
        return mask
    debt_series = get_series(frame, ["debt_to_equity", "de_ratio", "de_to_equity"])
    if debt_series is None:
        return mask

    debt_mask = pd.Series(True, index=frame.index)
    for idx, value in frame.iterrows():
        sector = str(value.get("sector", "")).strip().lower()
        if sector == "financials":
            continue
        debt_value = coerce_float(debt_series.loc[idx])
        if debt_value is not None and debt_value > max_debt_to_equity:
            debt_mask.at[idx] = False
    return mask & debt_mask


def apply_interest_filter(
    frame: pd.DataFrame, min_interest_coverage: Optional[float], mask: pd.Series
) -> pd.Series:
    """Applies interest coverage ratio screening, skipping debt-free companies."""
    if min_interest_coverage is None:
        return mask
    icr_series = get_series(
        frame, ["interest_coverage", "icr", "interest_coverage_ratio"]
    )
    if icr_series is None:
        return mask

    interest_mask = pd.Series(True, index=frame.index)
    for idx, value in frame.iterrows():
        label = str(value.get("icr_label", "")).strip().lower()
        if label == "debt free":
            continue
        icr_value = coerce_float(icr_series.loc[idx])
        if icr_value is not None and icr_value < min_interest_coverage:
            interest_mask.at[idx] = False
    return mask & interest_mask
