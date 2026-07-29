import streamlit as st
import pandas as pd

def render_result_table(df: pd.DataFrame):
    """
    Renders an interactive dashboard results table.
    
    Args:
        df (pd.DataFrame): Screened companies DataFrame
    """
    if df.empty:
        st.warning("No companies match the current filters.")
        return

    # Map database columns to user-friendly column names
    col_mapping = {
        'company_name': 'Company',
        'sector': 'Sector',
        'composite_quality_score': 'Composite Score',
        'return_on_equity_pct': 'ROE',
        'return_on_capital_employed_pct': 'ROCE',
        'revenue_cagr_5yr': 'Revenue CAGR',
        'pat_cagr_5yr': 'PAT CAGR',
        'debt_to_equity': 'Debt to Equity',
        'pe': 'PE',
        'pb': 'PB',
        'dividend_yield': 'Dividend Yield'
    }

    # Extract only the required columns that exist in the dataframe
    available_cols = [c for c in col_mapping.keys() if c in df.columns]
    display_df = df[available_cols].copy()
    display_df = display_df.rename(columns=col_mapping)

    # Reorder columns to match the request
    requested_order = [
        'Company', 'Sector', 'Composite Score', 'ROE', 'ROCE',
        'Revenue CAGR', 'PAT CAGR', 'Debt to Equity', 'PE', 'PB', 'Dividend Yield'
    ]
    actual_order = [c for c in requested_order if c in display_df.columns]
    display_df = display_df[actual_order]

    # Render interactive table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Company": st.column_config.TextColumn("Company"),
            "Sector": st.column_config.TextColumn("Sector"),
            "Composite Score": st.column_config.NumberColumn("Composite Score", format="%.2f"),
            "ROE": st.column_config.NumberColumn("ROE (%)", format="%.2f%%"),
            "ROCE": st.column_config.NumberColumn("ROCE (%)", format="%.2f%%"),
            "Revenue CAGR": st.column_config.NumberColumn("Revenue CAGR (5y)", format="%.2f%%"),
            "PAT CAGR": st.column_config.NumberColumn("PAT CAGR (5y)", format="%.2f%%"),
            "Debt to Equity": st.column_config.NumberColumn("Debt to Equity", format="%.2f"),
            "PE": st.column_config.NumberColumn("PE", format="%.2f"),
            "PB": st.column_config.NumberColumn("PB", format="%.2f"),
            "Dividend Yield": st.column_config.NumberColumn("Dividend Yield (%)", format="%.2f%%")
        }
    )
