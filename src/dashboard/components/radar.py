import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils import db
from src.dashboard.utils.helpers import extract_year_int


def load_radar_universe_data() -> pd.DataFrame:
    """
    Loads latest year data for all companies from the database, joins balance sheet
    for Current Assets / Current Liabilities, and calculates Current Ratio.
    """
    df_ratios = db.get_ratios()
    df_bs = db.get_bs()
    df_sectors = db.get_sectors()
    df_companies = db.get_companies()

    # Join financial_ratios with balance sheet (for other_asset and other_liabilities)
    df = pd.merge(
        df_ratios,
        df_bs[["company_id", "year", "other_asset", "other_liabilities"]],
        on=["company_id", "year"],
        how="left",
    )
    # Join with sectors (broad_sector and sub_sector)
    df = pd.merge(
        df,
        df_sectors[["company_id", "broad_sector", "sub_sector", "index_weight_pct"]],
        on="company_id",
        how="left",
    )
    # Join with company names
    df = pd.merge(
        df,
        df_companies[["id", "company_name"]],
        left_on="company_id",
        right_on="id",
        how="left",
    )

    # Rename sector columns to keep consistent
    if "broad_sector" in df.columns:
        df["sector"] = df["broad_sector"]

    # Calculate Current Ratio (other_asset / other_liabilities)
    def calc_cr(row):
        ca = row.get("other_asset")
        cl = row.get("other_liabilities")
        if pd.isnull(ca) or pd.isnull(cl) or cl <= 0:
            return 1.2  # Safe default Current Ratio for Indian Nifty 100 firms
        return round(ca / cl, 2)

    df["current_ratio"] = df.apply(calc_cr, axis=1)

    # Parse calendar years and filter for the latest year for each company
    df["year_int"] = df["year"].apply(extract_year_int)
    df_latest = (
        df.sort_values(by="year_int", ascending=False)
        .drop_duplicates(subset=["company_id"], keep="first")
        .copy()
    )

    # Fill clean values for radar metrics
    df_latest["roe"] = df_latest["return_on_equity_pct"].fillna(0.0)
    df_latest["roce"] = df_latest["return_on_capital_employed_pct"].fillna(0.0)
    df_latest["revenue_cagr"] = df_latest["revenue_cagr_5yr"].fillna(0.0)
    df_latest["pat_cagr"] = df_latest["pat_cagr_5yr"].fillna(0.0)
    df_latest["operating_margin"] = df_latest["operating_profit_margin_pct"].fillna(0.0)
    df_latest["composite_score"] = df_latest["composite_quality_score"].fillna(0.0)

    return df_latest


def calculate_normalized_radar_metrics(df_universe: pd.DataFrame) -> pd.DataFrame:
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

    df_norm = df_universe[["company_id", "company_name", "sector", "year"]].copy()

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
                scores = (
                    100.0 * (p90 - capped) / (p90 - p10)
                    if "capped" in locals()
                    else 100.0 * (p90 - clipped) / (p90 - p10)
                )
            else:
                scores = 100.0 * (clipped - p10) / (p90 - p10)
        else:
            scores = pd.Series(
                100.0 if not lower_is_better else 0.0, index=df_universe.index
            )

        df_norm[metric] = scores.round(2)

    return df_norm


def render_peer_radar(
    selected_company_id: str, df_raw: pd.DataFrame, df_norm: pd.DataFrame
):
    """
    Renders the peer comparison radar chart.
    """
    # Get selected company information
    row_company = df_raw[df_raw["company_id"] == selected_company_id]
    if row_company.empty:
        st.warning(f"Company {selected_company_id} not found.")
        return

    sector = row_company.iloc[0].get("sector")
    company_name = row_company.iloc[0].get("company_name") or selected_company_id

    # Selected company values
    row_norm_company = df_norm[df_norm["company_id"] == selected_company_id]
    if row_norm_company.empty:
        st.warning("Normalized metrics not found for the selected company.")
        return

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
    comp_values = [float(row_norm_company.iloc[0][m]) for m in metrics_list]

    # Sector average values (mean of normalized scores for companies in that sector)
    df_sector_norm = df_norm[df_norm["sector"] == sector]
    if not df_sector_norm.empty:
        sector_avg_values = [float(df_sector_norm[m].mean()) for m in metrics_list]
    else:
        sector_avg_values = [50.0] * len(metrics_list)

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

    # Draw Plotly radar
    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=comp_values + [comp_values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=company_name,
            line_color="#6c5ce7",
            fillcolor="rgba(108, 92, 231, 0.2)",
            hovertemplate="<b>%{theta}</b>: %{r:.1f} (Normalized)<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatterpolar(
            r=sector_avg_values + [sector_avg_values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=f"{sector} Sector Avg",
            line_color="#00b894",
            fillcolor="rgba(0, 184, 148, 0.1)",
            hovertemplate="<b>%{theta}</b>: %{r:.1f} (Normalized)<extra></extra>",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="rgba(255, 255, 255, 0.15)",
                color="#a0aec0",
            ),
            angularaxis=dict(gridcolor="rgba(255, 255, 255, 0.15)", color="#a0aec0"),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff", size=11),
        margin=dict(t=50, b=50, l=50, r=50),
        height=450,
    )

    st.plotly_chart(fig, use_container_width=True)
