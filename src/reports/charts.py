"""
Chart generation routines for Tearsheet PDF compilation.
Generates and saves the required Matplotlib charts as PNG artifacts.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from pathlib import Path

# Set seaborn theme for premium look
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']

def clean_years(years_series: pd.Series) -> list:
    """Helper to convert year strings to short years (e.g. 'Mar 2024' -> 'FY24')."""
    cleaned = []
    for val in years_series:
        val_str = str(val).strip()
        if len(val_str) >= 4 and val_str[-4:].isdigit():
            yr = val_str[-2:]
            cleaned.append(f"FY{yr}")
        else:
            cleaned.append(val_str)
    return cleaned

def generate_revenue_net_profit_charts(df: pd.DataFrame, company_id: str, out_dir: Path) -> tuple[Path, Path]:
    """Generates two separate high-res bar charts for Revenue and Net Profit (last 10 years)."""
    # Filter out TTM and sort chronologically
    df_clean = df[df["year"] != "TTM"].copy()
    if "year_int" in df_clean.columns:
        df_clean = df_clean.dropna(subset=["year_int"]).sort_values("year_int")
    df_last_10 = df_clean.tail(10)

    years = clean_years(df_last_10["year"])
    revenue = df_last_10["sales"].fillna(0).tolist()
    net_profit = df_last_10["net_profit"].fillna(0).tolist()

    # 1. Revenue Chart
    fig, ax = plt.subplots(figsize=(3.8, 2.2))
    bars = ax.bar(years, revenue, color="#1B365D", width=0.6, edgecolor="#11223B", linewidth=0.5)
    ax.set_title("Revenue (₹ Cr)", fontsize=9, fontweight="bold", color="#1B365D", pad=6)
    ax.tick_params(axis='both', which='major', labelsize=7)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    sns.despine(ax=ax, left=True, bottom=False, right=True, top=True)

    # Annotate bars
    max_rev = max(revenue) if revenue else 1.0
    ax.set_ylim(0, max_rev * 1.15)
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height:,.0f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 2),  # 2 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=6, fontweight="bold", color="#333333")

    rev_path = out_dir / f"{company_id}_revenue.png"
    plt.tight_layout()
    plt.savefig(rev_path, dpi=300, bbox_inches="tight")
    plt.close()

    # 2. Net Profit Chart
    fig, ax = plt.subplots(figsize=(3.8, 2.2))
    # Green fill for profit
    bars = ax.bar(years, net_profit, color="#2E7D32", width=0.6, edgecolor="#1B5E20", linewidth=0.5)
    ax.set_title("Net Profit (₹ Cr)", fontsize=9, fontweight="bold", color="#2E7D32", pad=6)
    ax.tick_params(axis='both', which='major', labelsize=7)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    sns.despine(ax=ax, left=True, bottom=False, right=True, top=True)

    # Annotate bars
    max_prof = max(net_profit) if net_profit else 1.0
    min_prof = min(net_profit) if net_profit else 0.0
    if min_prof < 0:
        ax.set_ylim(min_prof * 1.15, max_prof * 1.15)
    else:
        ax.set_ylim(0, max_prof * 1.15)

    for bar in bars:
        height = bar.get_height()
        va_dir = 'bottom' if height >= 0 else 'top'
        y_off = 2 if height >= 0 else -8
        ax.annotate(f"{height:,.0f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, y_off),
                    textcoords="offset points",
                    ha='center', va=va_dir, fontsize=6, fontweight="bold", color="#333333")

    prof_path = out_dir / f"{company_id}_net_profit.png"
    plt.tight_layout()
    plt.savefig(prof_path, dpi=300, bbox_inches="tight")
    plt.close()

    return rev_path, prof_path

def generate_roe_roce_chart(df: pd.DataFrame, company_id: str, out_dir: Path) -> Path:
    """Generates a high-res line chart showing ROE & ROCE trend over the last 10 years."""
    df_clean = df[df["year"] != "TTM"].copy()
    if "year_int" in df_clean.columns:
        df_clean = df_clean.dropna(subset=["year_int"]).sort_values("year_int")
    df_last_10 = df_clean.tail(10)

    years = clean_years(df_last_10["year"])
    roe = df_last_10["return_on_equity_pct"].tolist()
    roce = df_last_10["return_on_capital_employed_pct"].tolist()

    fig, ax = plt.subplots(figsize=(7.8, 2.2))
    
    # Plot lines with markers
    ax.plot(years, roe, marker='o', markersize=4, color="#1B365D", linewidth=1.8, label="Return on Equity (ROE)")
    ax.plot(years, roce, marker='s', markersize=4, color="#D4AF37", linewidth=1.8, label="Return on Capital Employed (ROCE)")

    ax.set_title("ROE & ROCE Historical Trend (%)", fontsize=10, fontweight="bold", color="#1B365D", pad=6)
    ax.tick_params(axis='both', which='major', labelsize=8)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(fontsize=8, loc="upper left")
    sns.despine(ax=ax, left=True, bottom=False, right=True, top=True)

    # Annotate points
    for i, (yr, val_roe, val_roce) in enumerate(zip(years, roe, roce)):
        if pd.notnull(val_roe):
            ax.annotate(f"{val_roe:.1f}%", (yr, val_roe), textcoords="offset points", xytext=(0, 6), ha='center', fontsize=6, fontweight="bold", color="#1B365D")
        if pd.notnull(val_roce):
            ax.annotate(f"{val_roce:.1f}%", (yr, val_roce), textcoords="offset points", xytext=(0, -10), ha='center', fontsize=6, fontweight="bold", color="#B48E1B")

    # Leave room for annotations
    all_vals = [v for v in roe + roce if pd.notnull(v)]
    if all_vals:
        ax.set_ylim(min(all_vals) - 5, max(all_vals) + 8)

    trend_path = out_dir / f"{company_id}_roe_roce_trend.png"
    plt.tight_layout()
    plt.savefig(trend_path, dpi=300, bbox_inches="tight")
    plt.close()

    return trend_path

def generate_balancesheet_composition_chart(df: pd.DataFrame, company_id: str, out_dir: Path) -> Path:
    """Generates stacked bar chart for Balance Sheet composition (Equity, Borrowings, Other Liabilities)."""
    df_clean = df[df["year"] != "TTM"].copy()
    if "year_int" in df_clean.columns:
        df_clean = df_clean.dropna(subset=["year_int"]).sort_values("year_int")
    df_last_10 = df_clean.tail(10)

    years = clean_years(df_last_10["year"])
    
    # Equity = reserves + equity_capital
    equity = (df_last_10["reserves"].fillna(0) + df_last_10["equity_capital"].fillna(0)).tolist()
    borrowings = df_last_10["borrowings"].fillna(0).tolist()
    other_liab = df_last_10["other_liabilities"].fillna(0).tolist()

    fig, ax = plt.subplots(figsize=(3.8, 2.2))

    # Stacked bars
    b1 = ax.bar(years, equity, color="#1B365D", width=0.55, label="Equity (Capital + Reserves)", edgecolor="#0F2038", linewidth=0.5)
    b2 = ax.bar(years, borrowings, bottom=equity, color="#D4AF37", width=0.55, label="Borrowings", edgecolor="#937926", linewidth=0.5)
    bottom_3 = np.array(equity) + np.array(borrowings)
    b3 = ax.bar(years, other_liab, bottom=bottom_3, color="#90A4AE", width=0.55, label="Other Liabilities", edgecolor="#607D8B", linewidth=0.5)

    ax.set_title("Balance Sheet Composition (₹ Cr)", fontsize=9, fontweight="bold", color="#1B365D", pad=6)
    ax.tick_params(axis='both', which='major', labelsize=7)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(fontsize=6, loc="upper left")
    sns.despine(ax=ax, left=True, bottom=False, right=True, top=True)

    bs_path = out_dir / f"{company_id}_balancesheet_composition.png"
    plt.tight_layout()
    plt.savefig(bs_path, dpi=300, bbox_inches="tight")
    plt.close()

    return bs_path

def generate_cashflow_waterfall_chart(cf_row: pd.Series, company_id: str, out_dir: Path) -> Path:
    """Generates waterfall chart for CFO -> CFI -> CFF -> Net Cash Flow for the latest year."""
    cfo = cf_row.get("operating_activity", 0.0)
    cfi = cf_row.get("investing_activity", 0.0)
    cff = cf_row.get("financing_activity", 0.0)
    net_cf = cf_row.get("net_cash_flow", 0.0)

    # If any is NaN, fill with 0.0
    cfo = 0.0 if pd.isna(cfo) else cfo
    cfi = 0.0 if pd.isna(cfi) else cfi
    cff = 0.0 if pd.isna(cff) else cff
    net_cf = 0.0 if pd.isna(net_cf) else net_cf

    categories = ['CFO', 'CFI', 'CFF', 'Net Cash']
    
    # Calculate bottom and heights
    # CFO starts at 0
    # CFI starts at CFO
    # CFF starts at CFO + CFI
    # Net Cash starts at 0
    bottoms = [0, cfo, cfo + cfi, 0]
    heights = [cfo, cfi, cff, net_cf]
    
    # Determine colors
    colors_list = []
    for idx, h in enumerate(heights):
        if idx == 3:
            colors_list.append("#1B365D") # Navy for Net Cash
        else:
            colors_list.append("#2E7D32" if h >= 0 else "#C62828") # Green for positive, Red for negative

    fig, ax = plt.subplots(figsize=(3.8, 2.2))
    
    # Draw bars
    bars = ax.bar(categories, heights, bottom=bottoms, color=colors_list, width=0.55, edgecolor="black", linewidth=0.5)
    
    ax.set_title(f"Cash Flow Breakdown: {cf_row.get('year', 'Latest')} (₹ Cr)", fontsize=9, fontweight="bold", color="#1B365D", pad=6)
    ax.tick_params(axis='both', which='major', labelsize=7)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    sns.despine(ax=ax, left=True, bottom=False, right=True, top=True)

    # Draw connection lines
    for i in range(3):
        # Line from top/bottom of bar i to top/bottom of bar i+1
        x1, x2 = i, i + 1
        y1 = bottoms[i] + heights[i]
        y2 = bottoms[i+1]
        ax.plot([x1, x2], [y1, y1], color="black", linestyle="--", linewidth=0.75)

    # Annotate values
    all_tops = [bottoms[i] + heights[i] for i in range(4)] + bottoms
    min_y = min(all_tops)
    max_y = max(all_tops)
    span = max_y - min_y
    ax.set_ylim(min_y - 0.15 * span if span else -10, max_y + 0.15 * span if span else 10)

    for i, bar in enumerate(bars):
        h = heights[i]
        top_y = bottoms[i] + h
        # Determine position of label
        va_dir = 'bottom' if h >= 0 else 'top'
        y_off = 3 if h >= 0 else -9
        ax.annotate(f"{h:+,.0f}",
                    xy=(bar.get_x() + bar.get_width() / 2, top_y),
                    xytext=(0, y_off),
                    textcoords="offset points",
                    ha='center', va=va_dir, fontsize=6.5, fontweight="bold", color="#333333")

    # Add a horizontal line at y=0
    ax.axhline(0, color='black', linewidth=0.8, linestyle='-', alpha=0.3)

    cf_path = out_dir / f"{company_id}_cashflow_waterfall.png"
    plt.tight_layout()
    plt.savefig(cf_path, dpi=300, bbox_inches="tight")
    plt.close()

    return cf_path
