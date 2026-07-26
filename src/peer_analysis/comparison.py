"""
Peer Comparison Engine.
Coordinates data loading, grouping, percentile calculations, ranking, and report generation.
"""

from __future__ import annotations
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List

from src.config.settings import DB_PATH, OUTPUT_DIR
from src.peer_analysis.percentile import compute_percentiles, calculate_sector_statistics
from src.peer_analysis.summary import get_top_performers, get_bottom_performers


def extract_year_int(yr_val: str) -> Optional[int]:
    """Helper to extract year from date string (e.g. 'Mar 2024' -> 2024)."""
    import re
    if pd.isna(yr_val):
        return None
    if str(yr_val).strip().upper() == "TTM":
        return None
    m = re.search(r"\b(19\d\d|20\d\d)\b", str(yr_val))
    return int(m.group(1)) if m else None


def load_raw_ratios_data(db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads company details, sector info, and financial ratios from SQLite.
    """
    db_file = db_path or DB_PATH
    conn = sqlite3.connect(str(db_file))
    
    query = """
    SELECT 
        fr.company_id AS Company,
        s.broad_sector AS Sector,
        fr.return_on_equity_pct AS ROE,
        fr.return_on_capital_employed_pct AS ROCE,
        fr.revenue_cagr_5yr AS [Revenue CAGR],
        fr.pat_cagr_5yr AS [PAT CAGR],
        fr.debt_to_equity AS [Debt to Equity],
        fr.operating_profit_margin_pct AS [Operating Margin],
        fr.interest_coverage AS [Interest Coverage],
        fr.composite_quality_score AS [Composite Quality Score],
        fr.year
    FROM financial_ratios fr
    LEFT JOIN sectors s ON fr.company_id = s.company_id
    """
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
        
    return df


def run_peer_analysis(db_path: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Executes the peer percentile and ranking analysis.
    
    Returns:
        Tuple of (peer_comparison_df, sector_stats_df, top_performers_df, bottom_performers_df)
    """
    df = load_raw_ratios_data(db_path)
    
    # Fill missing sectors with 'Unclassified'
    df["Sector"] = df["Sector"].fillna("Unclassified")
    
    # Keep only the latest year for each company
    df["year_int"] = df["year"].apply(extract_year_int)
    # Sort by year_int descending, then keep first company record
    df_latest = df.sort_values(by="year_int", ascending=False).drop_duplicates(subset=["Company"], keep="first").copy()
    
    # Percentile KPIs config: Column Name -> lower_is_better
    kpi_configs = {
        "ROE": False,
        "ROCE": False,
        "Revenue CAGR": False,
        "PAT CAGR": False,
        "Operating Margin": False,
        "Debt to Equity": True,  # Lower is better
        "Interest Coverage": False,
        "Composite Quality Score": False
    }
    
    # Store calculated percentiles
    percentile_cols = {
        "ROE": "roe_percentile",
        "ROCE": "roce_percentile",
        "Revenue CAGR": "revenue_cagr_percentile",
        "PAT CAGR": "pat_cagr_percentile",
        "Operating Margin": "margin_percentile",
        "Debt to Equity": "de_percentile",
        "Interest Coverage": "interest_coverage_percentile",
        "Composite Quality Score": "quality_score_percentile"
    }
    
    # Initialize percentile columns
    for col in percentile_cols.values():
        df_latest[col] = 0.0
        
    # Group by Sector and compute percentiles & peer ranking
    ranked_groups = []
    
    for sector, group in df_latest.groupby("Sector"):
        # Calculate percentiles within the sector
        for kpi, pct_col in percentile_cols.items():
            group[pct_col] = compute_percentiles(group[kpi], lower_is_better=kpi_configs[kpi])
            
        # Assign Peer Rank based on Composite Quality Score descending
        # Ensure we sort by Composite Quality Score descending
        group_sorted = group.sort_values(by="Composite Quality Score", ascending=False).copy()
        
        # Sequentially assign ranks (1, 2, 3...)
        group_sorted["Peer Rank"] = range(1, len(group_sorted) + 1)
        
        ranked_groups.append(group_sorted)
        
    df_ranked = pd.concat(ranked_groups).reset_index(drop=True)
    
    # 1. Create Peer Comparison Dataset
    peer_comparison = df_ranked.copy()
    
    # Map and rename columns to suggested names
    peer_comparison_export = pd.DataFrame({
        "Company": peer_comparison["Company"],
        "Sector": peer_comparison["Sector"],
        "Peer Rank": peer_comparison["Peer Rank"],
        "Composite Score": peer_comparison["Composite Quality Score"],
        "ROE Percentile": peer_comparison["roe_percentile"],
        "ROCE Percentile": peer_comparison["roce_percentile"],
        "Revenue CAGR Percentile": peer_comparison["revenue_cagr_percentile"],
        "PAT CAGR Percentile": peer_comparison["pat_cagr_percentile"],
        "Debt to Equity Percentile": peer_comparison["de_percentile"],
        "Operating Margin Percentile": peer_comparison["margin_percentile"],
        "Interest Coverage Percentile": peer_comparison["interest_coverage_percentile"]
    })
    
    # 2. Calculate Sector Statistics on raw KPIs
    kpis_to_stat = [
        "ROE", "ROCE", "Revenue CAGR", "PAT CAGR", 
        "Operating Margin", "Debt to Equity", "Interest Coverage", "Composite Quality Score"
    ]
    sector_statistics = calculate_sector_statistics(df_latest, kpis_to_stat)
    
    # 3. Identify Top & Bottom Performers (Top 3 and Bottom 3 per Sector)
    top_performers = get_top_performers(df_ranked, n=3)
    bottom_performers = get_bottom_performers(df_ranked, n=3)
    
    # Clean summaries for export
    summary_cols = ["Company", "Sector", "Peer Rank", "Composite Quality Score"]
    top_performers_export = top_performers[summary_cols].rename(columns={"Composite Quality Score": "Composite Score"}).copy()
    bottom_performers_export = bottom_performers[summary_cols].rename(columns={"Composite Quality Score": "Composite Score"}).copy()
    
    # 4. Export Results
    csv_dir = OUTPUT_DIR / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    
    peer_comparison_export.to_csv(csv_dir / "peer_comparison.csv", index=False)
    sector_statistics.to_csv(csv_dir / "sector_statistics.csv", index=False)
    top_performers_export.to_csv(csv_dir / "top_performers.csv", index=False)
    bottom_performers_export.to_csv(csv_dir / "bottom_performers.csv", index=False)
    
    return peer_comparison_export, sector_statistics, top_performers_export, bottom_performers_export


if __name__ == "__main__":
    run_peer_analysis()
