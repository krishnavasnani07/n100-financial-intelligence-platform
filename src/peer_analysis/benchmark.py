"""
Benchmarking Engine.
Compares individual company KPIs against sector benchmarks (mean, median).
"""

from __future__ import annotations
import pandas as pd
from typing import List


def benchmark_against_sector(df: pd.DataFrame, kpis: List[str]) -> pd.DataFrame:
    """
    Benchmarks each company's KPIs against its sector's mean and median.
    
    Adds comparison columns:
        - {kpi}_vs_sector_mean (absolute difference)
        - {kpi}_pct_of_sector_median (ratio to median in %)
    """
    benchmarked = df.copy()
    
    for kpi in kpis:
        if kpi not in benchmarked.columns:
            continue
            
        # Group by Sector and calculate mean and median
        means = benchmarked.groupby("Sector")[kpi].transform("mean")
        medians = benchmarked.groupby("Sector")[kpi].transform("median")
        
        # Calculate comparison metrics
        benchmarked[f"{kpi}_vs_sector_mean"] = (benchmarked[kpi] - means).round(4)
        
        # Avoid division by zero
        def safe_pct(val, med):
            if pd.isna(val) or pd.isna(med) or med == 0:
                return None
            return round((val / med) * 100.0, 2)
            
        benchmarked[f"{kpi}_pct_of_sector_median"] = benchmarked.apply(
            lambda r: safe_pct(r[kpi], medians.loc[r.name]), axis=1
        )
        
    return benchmarked
