import pandas as pd
import streamlit as st

from src.dashboard.components.bubble_chart import render_sector_bubble_chart
from src.dashboard.utils import db
from src.screener.presets import load_screener_master_data

st.markdown(
    "<h1 style='font-weight:800;'>🏭 Sector Analysis</h1>", unsafe_allow_html=True
)
st.markdown(
    "<p style='color:#8892b0; margin-top:-15px;'>Compare sector landscape and performance distributions among Nifty 100 constituents.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")


# Load master screener dataset
@st.cache_data(ttl=600)
def get_cached_sector_data() -> pd.DataFrame:
    """Get cached sector data."""
    try:
        # load_screener_master_data has latest year records joined with prices and sector weight
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
        st.error(f"Error loading master sector data: {e}")
        return pd.DataFrame()


df_master = get_cached_sector_data()

if df_master.empty:
    st.warning("Database contains no data or could not be loaded.")
    st.stop()

# Sector selection dropdown
sectors_list = sorted(df_master["sector"].dropna().unique())
selected_sector = st.selectbox("Select Broad Sector to Analyze:", sectors_list)

if not selected_sector:
    st.info("Please select a sector.")
    st.stop()

# Filter by selected sector
df_sector = df_master[df_master["sector"] == selected_sector].copy()

# Render bubble chart
render_sector_bubble_chart(df_sector, selected_sector)

st.markdown("---")
st.markdown("### 📊 Sector Performance Summary")

# Sector summary KPIs
if not df_sector.empty:
    col1, col2, col3, col4 = st.columns(4)

    med_roe = df_sector["return_on_equity_pct"].median()

    # Filter positive PE values for median calculation
    valid_pe = df_sector[df_sector["pe"] > 0]["pe"]
    med_pe = valid_pe.median() if not valid_pe.empty else float("nan")

    med_rev_cagr = df_sector["revenue_cagr_5yr"].median()
    avg_composite = df_sector["composite_quality_score"].mean()

    with col1:
        st.metric(
            label="Median ROE",
            value=f"{med_roe:.2f}%" if pd.notnull(med_roe) else "N/A",
        )
    with col2:
        st.metric(
            label="Median PE Ratio",
            value=f"{med_pe:.2f}x" if pd.notnull(med_pe) else "N/A",
        )
    with col3:
        st.metric(
            label="Median Revenue CAGR (5y)",
            value=f"{med_rev_cagr:.2f}%" if pd.notnull(med_rev_cagr) else "N/A",
        )
    with col4:
        st.metric(
            label="Avg Composite Score",
            value=f"{avg_composite:.2f}" if pd.notnull(avg_composite) else "N/A",
        )
else:
    st.info("No statistics available for this sector.")
