import pandas as pd
import streamlit as st


def render_top_companies_table(df: pd.DataFrame):
    """
    Renders a clean, styled table of top companies based on composite scores.

    Args:
        df (pd.DataFrame): DataFrame containing companies with rank, name, composite score, ROE, and sector.
    """
    # Clean and rename columns for display
    cols_to_use = []
    col_mapping = {}

    if "overall_rank" in df.columns:
        cols_to_use.append("overall_rank")
        col_mapping["overall_rank"] = "Rank"
    elif "Rank" in df.columns:
        cols_to_use.append("Rank")

    if "company_name" in df.columns:
        cols_to_use.append("company_name")
        col_mapping["company_name"] = "Company"
    elif "Company" in df.columns:
        cols_to_use.append("Company")

    if "composite_quality_score" in df.columns:
        cols_to_use.append("composite_quality_score")
        col_mapping["composite_quality_score"] = "Composite Score"
    elif "Composite Score" in df.columns:
        cols_to_use.append("Composite Score")

    if "return_on_equity_pct" in df.columns:
        cols_to_use.append("return_on_equity_pct")
        col_mapping["return_on_equity_pct"] = "ROE"
    elif "roe_percentage" in df.columns:
        cols_to_use.append("roe_percentage")
        col_mapping["roe_percentage"] = "ROE"
    elif "ROE" in df.columns:
        cols_to_use.append("ROE")

    if "sector" in df.columns:
        cols_to_use.append("sector")
        col_mapping["sector"] = "Sector"
    elif "broad_sector" in df.columns:
        cols_to_use.append("broad_sector")
        col_mapping["broad_sector"] = "Sector"
    elif "Sector" in df.columns:
        cols_to_use.append("Sector")

    display_df = df[cols_to_use].copy()
    display_df = display_df.rename(columns=col_mapping)

    # Render using native streamlit dataframe widget with neat column formatting
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", format="%d"),
            "Composite Score": st.column_config.NumberColumn(
                "Composite Score", format="%.2f"
            ),
            "ROE": st.column_config.NumberColumn("ROE (%)", format="%.2f%%"),
            "Company": st.column_config.TextColumn("Company"),
            "Sector": st.column_config.TextColumn("Sector"),
        },
    )
