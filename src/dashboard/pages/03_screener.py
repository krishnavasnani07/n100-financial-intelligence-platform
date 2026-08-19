import pandas as pd
import streamlit as st

from src.dashboard.components.download import render_download_button
from src.dashboard.components.result_table import render_result_table
from src.dashboard.components.slider_filters import render_slider_filters
from src.dashboard.utils import db
from src.screener.engine import filter_companies
from src.screener.presets import load_screener_master_data

st.markdown(
    "<h1 style='font-weight:800;'>🔍 Investment Screener</h1>", unsafe_allow_html=True
)
st.markdown(
    "<p style='color:#8892b0; margin-top:-15px;'>Filter Nifty 100 companies dynamically based on key financial metrics or use preset templates.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")


# Cache data loading for optimal responsiveness
@st.cache_data(ttl=600)
def get_cached_screener_data() -> pd.DataFrame:
    """Get cached screener data."""
    try:
        df = load_screener_master_data()
        df_companies = db.get_companies()
        df = pd.merge(
            df,
            df_companies[["id", "company_name"]],
            left_on="company_id",
            right_on="id",
            how="left",
        )
        return df
    except Exception as e:
        st.error(f"Error loading master screener data: {e}")
        return pd.DataFrame()


df_master = get_cached_screener_data()

if df_master.empty:
    st.warning("Database contains no data or could not be loaded.")
    st.stop()

# Render sliders in the sidebar and get values
slider_vals = render_slider_filters()

# Map sliders to engine configuration keys
filters_config = {
    "min_roe": slider_vals["min_roe"],
    "max_debt_to_equity": slider_vals["max_debt_to_equity"],
    "min_fcf": slider_vals["min_fcf"],
    "min_revenue_cagr_5yr": slider_vals["min_revenue_cagr_5yr"],
    "min_pat_cagr_5yr": slider_vals["min_pat_cagr_5yr"],
    "min_operating_profit_margin": slider_vals["min_operating_margin"],
    "max_pe": slider_vals["max_pe"],
    "max_pb": slider_vals["max_pb"],
    "min_dividend_yield": slider_vals["min_dividend_yield"],
    "min_interest_coverage": slider_vals["min_interest_coverage"],
}

# Run the filtering engine
df_filtered = filter_companies(df_master, {"filters": filters_config})

# Results Summary Banner
num_matches = len(df_filtered)

st.markdown(f"### 📊 {num_matches} Companies Match Your Filters")

if num_matches > 0:
    col1, col2, col3 = st.columns(3)

    avg_score = df_filtered["composite_quality_score"].mean()
    highest_roe = df_filtered["return_on_equity_pct"].max()

    # Calculate average PE safely (excluding negative/null PE values)
    valid_pe = df_filtered[df_filtered["pe"] > 0]["pe"]
    avg_pe = valid_pe.mean() if not valid_pe.empty else float("nan")

    with col1:
        st.metric(
            label="Average Composite Score",
            value=f"{avg_score:.2f}" if pd.notnull(avg_score) else "N/A",
        )
    with col2:
        st.metric(
            label="Highest ROE (%)",
            value=f"{highest_roe:.2f}%" if pd.notnull(highest_roe) else "N/A",
        )
    with col3:
        st.metric(
            label="Average PE", value=f"{avg_pe:.2f}x" if pd.notnull(avg_pe) else "N/A"
        )
else:
    st.info("Try relaxing your custom filters to view matching companies.")

st.markdown("---")

# Render the dynamic table
render_result_table(df_filtered)

st.markdown("<br>", unsafe_allow_html=True)

# Render download button
if num_matches > 0:
    render_download_button(df_filtered)
