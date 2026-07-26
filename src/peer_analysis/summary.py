"""
Performance Summary Engine.
Identifies top and bottom performing companies in each sector.
"""

from __future__ import annotations
import pandas as pd


def get_top_performers(df: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    """
    Identifies the top N performers per sector based on Composite Quality Score.
    """
    # Ensure sorted by sector, then Composite Quality Score descending
    df_sorted = df.sort_values(by=["Sector", "Composite Quality Score"], ascending=[True, False])
    
    # Group by Sector and take first N
    top_perf = df_sorted.groupby("Sector").head(n)
    return top_perf.copy()


def get_bottom_performers(df: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    """
    Identifies the bottom N performers per sector based on Composite Quality Score.
    """
    # Ensure sorted by sector, then Composite Quality Score ascending
    df_sorted = df.sort_values(by=["Sector", "Composite Quality Score"], ascending=[True, True])
    
    # Group by Sector and take first N
    bottom_perf = df_sorted.groupby("Sector").head(n)
    
    # Sort them back by sector then Composite Quality Score descending for readability
    bottom_perf = bottom_perf.sort_values(by=["Sector", "Composite Quality Score"], ascending=[True, False])
    return bottom_perf.copy()
