import streamlit as st
import pandas as pd
from src.dashboard.utils.helpers import get_master_data
from src.dashboard.components.cards import kpi_card
from src.dashboard.components.charts import render_sector_donut_chart
from src.dashboard.components.tables import render_top_companies_table

st.title("🏠 Home Dashboard")

# Load master data
try:
    df_master = get_master_data()
except Exception as e:
    st.error("Unable to load data. Please verify the database is populated.")
    st.stop()

# Sidebar year filter
# Extract distinct years from master data that are in the 2019-2024 range
available_years = sorted([int(y) for y in df_master['year_int'].dropna().unique() if 2019 <= y <= 2024])
if not available_years:
    available_years = [2019, 2020, 2021, 2022, 2023, 2024]
    
selected_year = st.sidebar.selectbox("Select Filter Year", available_years, index=len(available_years)-1)

# Filter by selected year
df_filtered = df_master[df_master['year_int'] == selected_year].copy()

# KPIs Calculations
avg_roe = df_filtered['return_on_equity_pct'].mean()
median_pe = df_filtered['pe'].median()
median_de = df_filtered['debt_to_equity'].median()
total_companies = df_filtered['company_id'].nunique()
median_rev_cagr = df_filtered['revenue_cagr_5yr'].median()
debt_free_count = (df_filtered['debt_to_equity'] == 0).sum()

# Render 6 KPI cards in a single row
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    kpi_card("Average ROE", f"{avg_roe:.2f}%" if pd.notnull(avg_roe) else "N/A", "Avg Return on Equity", "positive" if (avg_roe or 0) >= 15 else "neutral")
with col2:
    kpi_card("Median PE", f"{median_pe:.2f}x" if pd.notnull(median_pe) else "N/A", "Median Price/Earnings", "positive" if (median_pe or 99) < 25 else "neutral")
with col3:
    kpi_card("Median D/E", f"{median_de:.2f}x" if pd.notnull(median_de) else "N/A", "Median Debt to Equity", "positive" if (median_de or 99) < 0.5 else "neutral")
with col4:
    kpi_card("Total Companies", str(total_companies), "Nifty 100 Coverage", "neutral")
with col5:
    kpi_card("Median Rev CAGR", f"{median_rev_cagr:.2f}%" if pd.notnull(median_rev_cagr) else "N/A", "5-Year Revenue CAGR", "positive" if (median_rev_cagr or 0) >= 10 else "neutral")
with col6:
    kpi_card("Debt-Free Cos", str(debt_free_count), "Companies with D/E = 0", "positive" if debt_free_count > 0 else "neutral")

st.markdown("---")

# Layout for chart and table
col_chart, col_table = st.columns([1.1, 1.0])

with col_chart:
    st.subheader("Sector Distribution")
    render_sector_donut_chart(df_filtered)

with col_table:
    st.subheader("Top 5 Companies (Quality Score)")
    if not df_filtered.empty:
        df_top5 = df_filtered.sort_values(by="composite_quality_score", ascending=False).head(5).copy()
        df_top5['overall_rank'] = range(1, len(df_top5) + 1)
        render_top_companies_table(df_top5)
    else:
        st.info("No companies found for this year.")
