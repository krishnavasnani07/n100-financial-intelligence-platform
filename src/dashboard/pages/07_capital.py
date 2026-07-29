import streamlit as st
import pandas as pd
from src.dashboard.utils import db
from src.screener.presets import load_screener_master_data
from src.dashboard.components.treemap import classify_company_capital_allocation, render_capital_allocation_treemap

st.markdown("<h1 style='font-weight:800;'>💰 Capital Allocation Map</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#8892b0; margin-top:-15px;'>Categorize Nifty 100 constituents based on their historical capital allocation efficiency, growth reinvestment, and payout strategies.</p>", unsafe_allow_html=True)
st.markdown("---")

# Load and classify master data
@st.cache_data(ttl=600)
def get_classified_capital_data() -> pd.DataFrame:
    try:
        df = load_screener_master_data()
        df_companies = db.get_companies()
        df = pd.merge(df, df_companies[['id', 'company_name']], left_on='company_id', right_on='id', how='left')
        
        # Apply classification
        df['category'] = df.apply(classify_company_capital_allocation, axis=1)
        return df
    except Exception as e:
        st.error(f"Error loading and classifying capital allocation data: {e}")
        return pd.DataFrame()

df_classified = get_classified_capital_data()

if df_classified.empty:
    st.warning("Database contains no data or could not be loaded.")
    st.stop()

# Treemap view
render_capital_allocation_treemap(df_classified)

st.markdown("---")
st.markdown("### 📋 Category Detail Browser")

# Dropdown to filter by category
categories_list = ["All Categories"] + sorted(list(df_classified['category'].unique()))
selected_category = st.selectbox(
    "Select Capital Allocation Category to View constituents:",
    categories_list
)

# Filter dataframe
if selected_category == "All Categories":
    df_filtered = df_classified
else:
    df_filtered = df_classified[df_classified['category'] == selected_category]

# Columns to show in table
cols_to_show = [
    'company_id', 'company_name', 'sector', 'category',
    'composite_quality_score', 'return_on_equity_pct', 'debt_to_equity',
    'pe', 'dividend_yield', 'free_cash_flow_cr'
]
df_table = df_filtered[cols_to_show].copy()
df_table.rename(columns={
    'company_id': 'Ticker',
    'company_name': 'Company',
    'sector': 'Sector',
    'category': 'Category',
    'composite_quality_score': 'Composite Score',
    'return_on_equity_pct': 'ROE',
    'debt_to_equity': 'Debt to Equity',
    'pe': 'PE',
    'dividend_yield': 'Dividend Yield',
    'free_cash_flow_cr': 'Free Cash Flow'
}, inplace=True)

# Render table
st.dataframe(
    df_table,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Ticker": st.column_config.TextColumn("Ticker"),
        "Company": st.column_config.TextColumn("Company"),
        "Sector": st.column_config.TextColumn("Sector"),
        "Category": st.column_config.TextColumn("Category"),
        "Composite Score": st.column_config.NumberColumn("Composite Score", format="%.2f"),
        "ROE": st.column_config.NumberColumn("ROE (%)", format="%.2f%%"),
        "Debt to Equity": st.column_config.NumberColumn("Debt to Equity", format="%.2f"),
        "PE": st.column_config.NumberColumn("PE", format="%.2f"),
        "Dividend Yield": st.column_config.NumberColumn("Dividend Yield (%)", format="%.2f%%"),
        "Free Cash Flow": st.column_config.NumberColumn("FCF (INR Cr)", format="₹%d Cr")
    }
)
