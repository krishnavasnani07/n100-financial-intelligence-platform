"""
Trend Charts Generator.
Generates multi-panel line plots for historical Revenue, Net Profit, ROE, and OPM.
"""

from __future__ import annotations
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional

from src.config.settings import DB_PATH, OUTPUT_DIR
from src.screener.presets import extract_year_int


def generate_trend_charts(company_id: str, save_path: Optional[Path] = None, db_path: Optional[Path] = None) -> Path:
    """
    Generates a 4-panel line chart showing historical trends for:
    1. Revenue (Cr)
    2. PAT / Net Profit (Cr)
    3. ROE (%)
    4. Operating Margin (%)
    """
    db_file = db_path or DB_PATH
    conn = sqlite3.connect(str(db_file))
    
    query = """
    SELECT 
        fr.year,
        pl.sales as revenue,
        pl.net_profit as pat,
        fr.return_on_equity_pct as roe,
        fr.operating_profit_margin_pct as margin
    FROM financial_ratios fr
    LEFT JOIN profitandloss pl ON fr.company_id = pl.company_id AND fr.year = pl.year
    WHERE fr.company_id = ?
    """
    try:
        df = pd.read_sql_query(query, conn, params=(company_id,))
    finally:
        conn.close()
        
    if df.empty:
        raise ValueError(f"No historical data found for company: {company_id}")
        
    # Sort by year chronologically
    df['year_int'] = df['year'].apply(extract_year_int)
    # Exclude TTM or null years to ensure a clean chronological series
    df = df.dropna(subset=['year_int']).sort_values(by='year_int').copy()
    
    if len(df) < 2:
        # Fallback if there is very little history (e.g. fill with duplicate or dummy)
        pass
        
    # Setup subplots
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"Historical Financial Trends: {company_id}", fontsize=16, fontweight='bold', color='#1B365D', y=0.98)
    
    # 1. Revenue Plot
    ax1 = axes[0, 0]
    ax1.plot(df['year'], df['revenue'], marker='o', linewidth=2, color='#1F77B4')
    ax1.set_title("Revenue Trend (Cr)", fontsize=12, fontweight='bold', color='#333333')
    ax1.set_ylabel("Sales (INR Cr)", fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.5)
    for x, y in zip(df['year'], df['revenue']):
        if pd.notnull(y):
            ax1.annotate(f"{y:,.0f}", (x, y), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)
            
    # 2. PAT Plot
    ax2 = axes[0, 1]
    ax2.plot(df['year'], df['pat'], marker='o', linewidth=2, color='#2CA02C')
    ax2.set_title("PAT Trend (Cr)", fontsize=12, fontweight='bold', color='#333333')
    ax2.set_ylabel("Net Profit (INR Cr)", fontsize=10)
    ax2.grid(True, linestyle='--', alpha=0.5)
    for x, y in zip(df['year'], df['pat']):
        if pd.notnull(y):
            ax2.annotate(f"{y:,.0f}", (x, y), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)
            
    # 3. ROE Plot
    ax3 = axes[1, 0]
    ax3.plot(df['year'], df['roe'], marker='o', linewidth=2, color='#FF7F0E')
    ax3.set_title("Return on Equity (%)", fontsize=12, fontweight='bold', color='#333333')
    ax3.set_ylabel("ROE (%)", fontsize=10)
    ax3.grid(True, linestyle='--', alpha=0.5)
    for x, y in zip(df['year'], df['roe']):
        if pd.notnull(y):
            ax3.annotate(f"{y:.1f}%", (x, y), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)
            
    # 4. Operating Margin Plot
    ax4 = axes[1, 1]
    ax4.plot(df['year'], df['margin'], marker='o', linewidth=2, color='#D62728')
    ax4.set_title("Operating Margin Trend (%)", fontsize=12, fontweight='bold', color='#333333')
    ax4.set_ylabel("OPM (%)", fontsize=10)
    ax4.grid(True, linestyle='--', alpha=0.5)
    for x, y in zip(df['year'], df['margin']):
        if pd.notnull(y):
            ax4.annotate(f"{y:.1f}%", (x, y), textcoords="offset points", xytext=(0,10), ha='center', fontsize=8)
            
    plt.tight_layout()
    
    # Save the multi-panel chart
    out_file = save_path or (OUTPUT_DIR / "charts" / "trends" / f"{company_id}_trends.png")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    return out_file
