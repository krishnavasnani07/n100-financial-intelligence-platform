import streamlit as st
import pandas as pd

def render_download_button(df: pd.DataFrame, filename: str = "screener_results.csv"):
    """
    Renders a button to download the current dataframe as a CSV.
    The exported columns will match the columns displayed in the results table.
    """
    if df.empty:
        return

    # Keep and rename the exact visible columns
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

    available_cols = [c for c in col_mapping.keys() if c in df.columns]
    export_df = df[available_cols].copy()
    export_df = export_df.rename(columns=col_mapping)

    requested_order = [
        'Company', 'Sector', 'Composite Score', 'ROE', 'ROCE',
        'Revenue CAGR', 'PAT CAGR', 'Debt to Equity', 'PE', 'PB', 'Dividend Yield'
    ]
    actual_order = [c for c in requested_order if c in export_df.columns]
    export_df = export_df[actual_order]

    # Convert to CSV
    csv_data = export_df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Export Results to CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        use_container_width=True
    )
