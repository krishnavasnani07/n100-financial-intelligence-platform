"""
Sector Heatmap Visualization Engine.
Generates heatmaps where rows are companies and columns are key financial metrics.
"""

from __future__ import annotations
import sqlite3
import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional

from src.config.settings import DB_PATH, OUTPUT_DIR
from src.screener.presets import extract_year_int


def generate_sector_heatmap(sector_name: str, save_path: Optional[Path] = None, db_path: Optional[Path] = None) -> Path:
    """
    Generates and saves a sector heatmap.
    Color intensity represents the company's percentile rank in the sector (green is best, red is worst),
    while the text annotation shows the raw metric value.
    """
    db_file = db_path or DB_PATH
    conn = sqlite3.connect(str(db_file))
    
    # Query all companies in the target sector joined with their latest financial ratios
    query = """
    SELECT 
        fr.company_id AS Company,
        s.broad_sector AS Sector,
        fr.year,
        fr.return_on_equity_pct AS ROE,
        fr.return_on_capital_employed_pct AS ROCE,
        fr.revenue_cagr_5yr AS Growth,
        fr.operating_profit_margin_pct AS Margin,
        fr.debt_to_equity AS [D/E],
        fr.composite_quality_score AS [Quality Score]
    FROM financial_ratios fr
    LEFT JOIN sectors s ON fr.company_id = s.company_id
    WHERE s.broad_sector = ?
    """
    try:
        df = pd.read_sql_query(query, conn, params=(sector_name,))
    finally:
        conn.close()
        
    if df.empty:
        raise ValueError(f"No data found for sector: {sector_name}")
        
    # Keep latest year for each company
    df['year_int'] = df['year'].apply(extract_year_int)
    df_latest = df.sort_values(by="year_int", ascending=False).drop_duplicates(subset=["Company"], keep="first").copy()
    
    # Select columns to display
    cols = ["ROE", "ROCE", "Growth", "Margin", "D/E", "Quality Score"]
    df_latest = df_latest.dropna(subset=["Company"])
    
    # Set Index to Company ID
    df_latest.set_index("Company", inplace=True)
    df_data = df_latest[cols].copy()
    
    # Fill NaN values with sector median for rendering safety
    for col in cols:
        median_val = df_data[col].median()
        if pd.isnull(median_val):
            df_data[col] = df_data[col].fillna(0.0)
        else:
            df_data[col] = df_data[col].fillna(median_val)
            
    # Calculate Score DataFrame (0 to 100, where green is always best)
    df_scores = pd.DataFrame(index=df_data.index)
    for col in cols:
        vals = df_data[col]
        min_v = vals.min()
        max_v = vals.max()
        
        if col == "D/E":
            # Lower is better
            if max_v > min_v:
                df_scores[col] = 100.0 * (max_v - vals) / (max_v - min_v)
            else:
                df_scores[col] = 100.0
        else:
            # Higher is better
            if max_v > min_v:
                df_scores[col] = 100.0 * (vals - min_v) / (max_v - min_v)
            else:
                df_scores[col] = 100.0
                
    # Create text annotations DataFrame containing the actual raw values
    df_annot = pd.DataFrame(index=df_data.index)
    for col in cols:
        def format_val(val, column_name):
            if column_name in ["ROE", "ROCE", "Growth", "Margin"]:
                return f"{val:.1f}%"
            elif column_name == "D/E":
                return f"{val:.2f}x"
            else:
                return f"{val:.1f}"
        df_annot[col] = df_data[col].apply(lambda v: format_val(v, col))
        
    # Plotting
    plt.figure(figsize=(10, max(6, len(df_data) * 0.4)))
    
    # Customize seaborn theme
    sns.set_theme(style="white")
    
    # Render Heatmap
    ax = sns.heatmap(
        df_scores,
        annot=df_annot,
        fmt="",
        cmap="RdYlGn",
        linewidths=0.5,
        cbar_kws={'label': 'Sector Performance Score (0-100)'},
        vmin=0,
        vmax=100
    )
    
    # Layout adjustments
    plt.title(f"Sector Performance Map: {sector_name} (Latest Year)", fontsize=14, fontweight='bold', color='#1B365D', pad=20)
    plt.xlabel("Key Performance Indicators (KPIs)", fontsize=11, fontweight='semibold', labelpad=10)
    plt.ylabel("Companies", fontsize=11, fontweight='semibold', labelpad=10)
    
    # Rotate axis labels for readability
    plt.xticks(rotation=30, ha='right')
    plt.yticks(rotation=0)
    
    plt.tight_layout()
    
    # Save image
    out_file = save_path or (OUTPUT_DIR / "charts" / "heatmaps" / f"{sector_name.lower().replace(' ', '_')}_heatmap.png")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return out_file
