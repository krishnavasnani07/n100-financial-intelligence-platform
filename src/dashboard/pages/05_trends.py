import pandas as pd
import streamlit as st

from src.dashboard.components.trend_chart import render_trend_charts
from src.dashboard.utils import db
from src.dashboard.utils.helpers import extract_year_int

st.markdown(
    "<h1 style='font-weight:800;'>📈 Trend Analysis</h1>", unsafe_allow_html=True
)
st.markdown(
    "<p style='color:#8892b0; margin-top:-15px;'>Inspect 10-year financial metrics and growth trends for any Nifty 100 company.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# Load companies
try:
    df_companies = db.get_companies()
except Exception:
    st.error("Unable to load data. Please build the database first.")
    st.stop()

if df_companies.empty:
    st.warning("No company records found.")
    st.stop()

# Company selector autocomplete search
company_options = [
    f"{row['id']} - {row['company_name']}" for _, row in df_companies.iterrows()
]
company_options.sort()
selected_option = st.selectbox("Select Company:", company_options)

if not selected_option:
    st.info("Please select a company to begin trend analysis.")
    st.stop()

selected_ticker = selected_option.split(" - ")[0].strip()

# Load company P&L and financial ratios
df_pl_all = db.get_pl()
df_ratios_all = db.get_ratios()

df_company_pl = df_pl_all[df_pl_all["company_id"] == selected_ticker].copy()
df_company_ratios = df_ratios_all[df_ratios_all["company_id"] == selected_ticker].copy()

if df_company_pl.empty and df_company_ratios.empty:
    st.warning("No historical financial data found for this company.")
    st.stop()

# Merge P&L and ratios datasets on year and company_id
df_history = pd.merge(
    df_company_pl,
    df_company_ratios,
    on=["company_id", "year"],
    how="outer",
    suffixes=("", "_ratio"),
)

df_history["year_int"] = df_history["year"].apply(extract_year_int)
df_history = df_history.dropna(subset=["year_int"]).sort_values("year_int")

# Map metric names to columns in the merged dataframe
METRIC_MAP = {
    "Revenue (Cr)": "sales",
    "Net Profit (Cr)": "net_profit",
    "Operating Profit (Cr)": "operating_profit",
    "EPS (₹)": "eps",
    "ROE (%)": "return_on_equity_pct",
    "ROCE (%)": "return_on_capital_employed_pct",
    "Debt to Equity (x)": "debt_to_equity",
    "Free Cash Flow (Cr)": "free_cash_flow_cr",
    "Interest Coverage (x)": "interest_coverage",
}

# Metric Selector: allow selecting up to three metrics
st.markdown("### Select Metrics (Max 3)")
selected_metrics = st.multiselect(
    "Choose up to three metrics to analyze:",
    options=list(METRIC_MAP.keys()),
    default=["Revenue (Cr)", "Net Profit (Cr)", "ROE (%)"],
    max_selections=3,
)

st.markdown("---")

# Render line charts
render_trend_charts(df_history, selected_metrics, METRIC_MAP)
