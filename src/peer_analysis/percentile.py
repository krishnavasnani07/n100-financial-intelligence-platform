"""
Percentile and Sector Statistics Engine.
Calculates percentile ranks for KPIs and computes statistical summaries by sector.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_percentiles(series: pd.Series, lower_is_better: bool = False) -> pd.Series:
    """
    Computes percentile ranks (0-100) for a series within a sector.

    If lower_is_better is True, lower values correspond to higher percentiles.
    Missing values (NaN) are excluded from the ranking and return NaN.
    """
    valid_series = series.dropna()
    if valid_series.empty:
        return pd.Series(np.nan, index=series.index)

    n = len(valid_series)
    if n == 1:
        # If only one company in the sector, it is in the 100th percentile
        res = pd.Series(np.nan, index=series.index)
        res.loc[valid_series.index] = 100.0
        return res

    # Ascending rank for higher-is-better, descending for lower-is-better
    ascending = not lower_is_better
    ranks = valid_series.rank(ascending=ascending, method="min")

    min_rank = ranks.min()
    max_rank = ranks.max()

    if max_rank > min_rank:
        # Linear scaling to 0-100
        scaled = 100.0 * (ranks - min_rank) / (max_rank - min_rank)
    else:
        # If all values are identical
        scaled = pd.Series(100.0, index=valid_series.index)

    res = pd.Series(np.nan, index=series.index)
    res.loc[valid_series.index] = scaled.round(2)
    return res


def calculate_sector_statistics(df: pd.DataFrame, kpis: list[str]) -> pd.DataFrame:
    """
    Computes sector-wise statistics (Mean, Median, Min, Max, Std Dev) for each KPI.

    Returns a long-format DataFrame with statistics.
    """
    stats_list = []

    # Group by Sector
    for sector, group in df.groupby("Sector"):
        for kpi in kpis:
            if kpi not in group.columns:
                continue

            series = group[kpi].dropna()

            if not series.empty:
                mean_val = round(float(series.mean()), 4)
                median_val = round(float(series.median()), 4)
                min_val = round(float(series.min()), 4)
                max_val = round(float(series.max()), 4)
                std_val = round(float(series.std()), 4) if len(series) > 1 else 0.0
            else:
                mean_val = np.nan
                median_val = np.nan
                min_val = np.nan
                max_val = np.nan
                std_val = np.nan

            stats_list.append(
                {
                    "Sector": sector,
                    "KPI": kpi,
                    "Mean": mean_val,
                    "Median": median_val,
                    "Minimum": min_val,
                    "Maximum": max_val,
                    "Standard Deviation": std_val,
                }
            )

    return pd.DataFrame(stats_list)
