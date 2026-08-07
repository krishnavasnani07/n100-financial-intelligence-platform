"""
Radar Chart Visualization Engine.
Generates single company and peer comparison radar (spider) charts.
"""

from __future__ import annotations

import math
import sqlite3

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt

from src.config.settings import DB_PATH, OUTPUT_DIR
from src.utils.helpers import extract_year_int


def load_universe_data(db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads latest year data for all companies from the database, joins balance sheet
    for Current Assets / Current Liabilities, and calculates Current Ratio.
    """
    db_file = db_path or DB_PATH
    conn = sqlite3.connect(str(db_file))

    query = """
    SELECT 
        fr.company_id,
        fr.year,
        fr.return_on_equity_pct as roe,
        fr.return_on_capital_employed_pct as roce,
        fr.revenue_cagr_5yr as revenue_cagr,
        fr.pat_cagr_5yr as pat_cagr,
        fr.operating_profit_margin_pct as operating_margin,
        bs.other_asset as current_assets,
        bs.other_liabilities as current_liabilities,
        fr.debt_to_equity,
        fr.composite_quality_score as composite_score
    FROM financial_ratios fr
    LEFT JOIN balancesheet bs ON fr.company_id = bs.company_id AND fr.year = bs.year
    """
    try:
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()

    # Calculate Current Ratio (other_asset / other_liabilities)
    def calc_cr(row):
        ca = row["current_assets"]
        cl = row["current_liabilities"]
        if pd.isnull(ca) or pd.isnull(cl) or cl <= 0:
            return 1.2  # Safe default Current Ratio for Indian Nifty 100 firms
        return round(ca / cl, 2)

    df["current_ratio"] = df.apply(calc_cr, axis=1)

    # Parse years and filter for the latest year for each company
    df["year_int"] = df["year"].apply(extract_year_int)
    df_latest = (
        df.sort_values(by="year_int", ascending=False)
        .drop_duplicates(subset=["company_id"], keep="first")
        .copy()
    )

    return df_latest


def calculate_normalized_metrics(df_universe: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes the 8 radar chart metrics to a 0-100 scale using winsorized min-max scaling.
    Higher score is always better (i.e. lower Debt-to-Equity yields higher score).
    """
    metrics_config = {
        "roe": False,
        "roce": False,
        "revenue_cagr": False,
        "pat_cagr": False,
        "operating_margin": False,
        "current_ratio": False,
        "debt_to_equity": True,  # Lower is better
        "composite_score": False,
    }

    df_norm = df_universe[["company_id", "year"]].copy()

    for metric, lower_is_better in metrics_config.items():
        series = df_universe[metric].dropna()
        if series.empty:
            df_norm[metric] = 50.0
            continue

        p10 = series.quantile(0.10)
        p90 = series.quantile(0.90)
        median_val = series.median()

        # Fill missing values with median
        filled = df_universe[metric].fillna(median_val)

        # Winsorize and Scale
        if p90 > p10:
            clipped = filled.clip(lower=p10, upper=p90)
            if lower_is_better:
                scores = 100.0 * (p90 - clipped) / (p90 - p10)
            else:
                scores = 100.0 * (clipped - p10) / (p90 - p10)
        else:
            scores = pd.Series(
                100.0 if not lower_is_better else 0.0, index=df_universe.index
            )

        df_norm[metric] = scores.round(2)

    return df_norm


def get_company_metrics(
    company_id: str, df_norm: pd.DataFrame, df_raw: pd.DataFrame
) -> Tuple[List[float], List[float]]:
    """Returns (normalized_values, raw_values) for the specified company."""
    norm_row = df_norm[df_norm["company_id"] == company_id]
    raw_row = df_raw[df_raw["company_id"] == company_id]

    metrics_list = [
        "roe",
        "roce",
        "revenue_cagr",
        "pat_cagr",
        "operating_margin",
        "current_ratio",
        "debt_to_equity",
        "composite_score",
    ]

    if norm_row.empty:
        # Defaults if company not found
        return [0.0] * 8, [0.0] * 8

    n_vals = [float(norm_row.iloc[0][m]) for m in metrics_list]
    r_vals = [
        float(raw_row.iloc[0][m]) if pd.notnull(raw_row.iloc[0][m]) else 0.0
        for m in metrics_list
    ]

    return n_vals, r_vals


def generate_single_radar(
    company_id: str, save_path: Optional[Path] = None, db_path: Optional[Path] = None
) -> Path:
    """
    Generates and saves a radar chart for a single company.
    """
    df_raw = load_universe_data(db_path)
    df_norm = calculate_normalized_metrics(df_raw)

    n_vals, r_vals = get_company_metrics(company_id, df_norm, df_raw)

    categories = [
        "ROE",
        "ROCE",
        "Revenue CAGR",
        "PAT CAGR",
        "Operating Margin",
        "Current Ratio",
        "Debt to Equity",
        "Composite Score",
    ]
    N = len(categories)

    # Close the loop
    plot_vals = n_vals + n_vals[:1]
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    # Visual Styling
    plt.figure(figsize=(7, 7))
    ax = plt.subplot(111, polar=True)

    # Set starting angle
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # Draw spokes
    plt.xticks(angles[:-1], categories, color="#333333", size=9, fontweight="semibold")

    # Draw radial lines / circles
    ax.set_rlabel_position(0)
    plt.yticks(
        [20, 40, 60, 80, 100], ["20", "40", "60", "80", "100"], color="#999999", size=8
    )
    plt.ylim(0, 100)

    # Grid customization
    ax.grid(color="#E5E5E5", linestyle="--", linewidth=0.7)

    # Plot company data
    ax.plot(
        angles,
        plot_vals,
        color="#1B365D",
        linewidth=2,
        linestyle="solid",
        label=company_id,
    )
    ax.fill(angles, plot_vals, color="#1B365D", alpha=0.15)

    # Chart Title
    plt.title(
        f"Financial Health & Quality Profile: {company_id}",
        size=14,
        color="#1B365D",
        fontweight="bold",
        pad=25,
    )

    # Save chart
    out_file = save_path or (
        OUTPUT_DIR / "charts" / "radar" / f"{company_id}_radar.png"
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()

    return out_file


def generate_peer_radar(
    company_a: str,
    company_b: str,
    save_path: Optional[Path] = None,
    db_path: Optional[Path] = None,
) -> Path:
    """
    Generates a peer comparison radar chart overlaying Company A and Company B.
    """
    df_raw = load_universe_data(db_path)
    df_norm = calculate_normalized_metrics(df_raw)

    a_n_vals, _ = get_company_metrics(company_a, df_norm, df_raw)
    b_n_vals, _ = get_company_metrics(company_b, df_norm, df_raw)

    categories = [
        "ROE",
        "ROCE",
        "Revenue CAGR",
        "PAT CAGR",
        "Operating Margin",
        "Current Ratio",
        "Debt to Equity",
        "Composite Score",
    ]
    N = len(categories)

    a_plot_vals = a_n_vals + a_n_vals[:1]
    b_plot_vals = b_n_vals + b_n_vals[:1]

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    # Visual Styling
    plt.figure(figsize=(8, 8))
    ax = plt.subplot(111, polar=True)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    plt.xticks(angles[:-1], categories, color="#333333", size=9, fontweight="semibold")

    ax.set_rlabel_position(0)
    plt.yticks(
        [20, 40, 60, 80, 100], ["20", "40", "60", "80", "100"], color="#999999", size=8
    )
    plt.ylim(0, 100)

    ax.grid(color="#E5E5E5", linestyle="--", linewidth=0.7)

    # Plot Company A (Navy Blue)
    ax.plot(
        angles,
        a_plot_vals,
        color="#1B365D",
        linewidth=2,
        linestyle="solid",
        label=company_a,
    )
    ax.fill(angles, a_plot_vals, color="#1B365D", alpha=0.15)

    # Plot Company B (Warm Amber/Coral)
    ax.plot(
        angles,
        b_plot_vals,
        color="#D9534F",
        linewidth=2,
        linestyle="solid",
        label=company_b,
    )
    ax.fill(angles, b_plot_vals, color="#D9534F", alpha=0.15)

    # Add Title and Legend
    plt.title(
        f"Peer Quality Comparison: {company_a} vs {company_b}",
        size=14,
        color="#1B365D",
        fontweight="bold",
        pad=25,
    )
    plt.legend(
        loc="upper right",
        bbox_to_anchor=(1.1, 1.1),
        frameon=True,
        facecolor="white",
        edgecolor="#E5E5E5",
    )

    # Save chart
    out_file = save_path or (
        OUTPUT_DIR / "charts" / "peer" / f"{company_a}_vs_{company_b}_radar.png"
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()

    return out_file
