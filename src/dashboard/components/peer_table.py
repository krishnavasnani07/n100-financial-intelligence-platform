import streamlit as st
import pandas as pd

def render_peer_table(df_sector: pd.DataFrame, selected_company_id: str):
    """
    Renders peer ranking table and sector summary statistics.
    """
    if df_sector.empty:
        st.warning("No peer data found in the sector.")
        return

    # Sort sector companies by composite score descending
    df_sorted = df_sector.sort_values(by="composite_quality_score", ascending=False).reset_index(drop=True)
    # Add Rank in sector
    df_sorted['Sector Rank'] = df_sorted.index + 1

    # Select columns
    display_cols = ['Sector Rank', 'company_id', 'company_name', 'composite_quality_score', 'return_on_equity_pct', 'return_on_capital_employed_pct', 'revenue_cagr_5yr', 'pat_cagr_5yr']
    df_display = df_sorted[display_cols].copy()

    # Rename columns for table headers
    df_display.rename(columns={
        'Sector Rank': 'Rank',
        'company_id': 'Ticker',
        'company_name': 'Company',
        'composite_quality_score': 'Composite Score',
        'return_on_equity_pct': 'ROE',
        'return_on_capital_employed_pct': 'ROCE',
        'revenue_cagr_5yr': 'Revenue CAGR',
        'pat_cagr_5yr': 'PAT CAGR'
    }, inplace=True)

    # Styling row for selected company
    def highlight_row(row):
        if row['Ticker'] == selected_company_id:
            # Highlight with a subtle background color
            return ['background-color: rgba(108, 92, 231, 0.25); font-weight: bold; border-left: 4px solid #6c5ce7;'] * len(row)
        return [''] * len(row)

    styled_df = df_display.style.apply(highlight_row, axis=1)

    st.subheader("Peer Rankings & KPIs")
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", format="%d"),
            "Ticker": st.column_config.TextColumn("Ticker"),
            "Company": st.column_config.TextColumn("Company"),
            "Composite Score": st.column_config.NumberColumn("Composite Score", format="%.2f"),
            "ROE": st.column_config.NumberColumn("ROE (%)", format="%.2f%%"),
            "ROCE": st.column_config.NumberColumn("ROCE (%)", format="%.2f%%"),
            "Revenue CAGR": st.column_config.NumberColumn("Revenue CAGR (5y)", format="%.2f%%"),
            "PAT CAGR": st.column_config.NumberColumn("PAT CAGR (5y)", format="%.2f%%")
        }
    )

    # Sector summary statistics
    st.markdown("---")
    st.subheader("📊 Sector Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    avg_score = df_sorted['composite_quality_score'].mean()
    max_score = df_sorted['composite_quality_score'].max()
    min_score = df_sorted['composite_quality_score'].min()
    med_score = df_sorted['composite_quality_score'].median()

    with col1:
        st.metric(label="Sector Average Score", value=f"{avg_score:.2f}")
    with col2:
        st.metric(label="Highest Score", value=f"{max_score:.2f}")
    with col3:
        st.metric(label="Lowest Score", value=f"{min_score:.2f}")
    with col4:
        st.metric(label="Median Score", value=f"{med_score:.2f}")
