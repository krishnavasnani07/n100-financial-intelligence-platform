import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from src.dashboard.utils import db
from src.screener.presets import load_screener_master_data
from src.dashboard.components.treemap import classify_company_capital_allocation, render_capital_allocation_treemap
from src.config.settings import OUTPUT_DIR

st.markdown("<h1 style='font-weight:800;'>💰 Capital Allocation Intelligence</h1>", unsafe_allow_html=True)
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

# Create tabs for interactive analysis
tab1, tab2 = st.tabs(["🗺️ Allocation Map", "🔄 Strategy Evolution & Transitions"])

with tab1:
    # Treemap view
    render_capital_allocation_treemap(df_classified)
    
    st.markdown("---")
    st.markdown("### 📋 Category Detail Browser")
    
    # Dropdown to filter by category
    categories_list = ["All Categories"] + sorted(list(df_classified['category'].unique()))
    selected_category = st.selectbox(
        "Select Capital Allocation Category to View constituents:",
        categories_list,
        key="treemap_category_select"
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

with tab2:
    st.subheader("Distribution of Allocation Strategies")
    
    summary_path = Path("output/capital_allocation_summary.csv")
    changes_path = Path("output/pattern_changes.csv")
    
    if summary_path.exists():
        df_summary = pd.read_csv(summary_path)
        
        # Render clean bar chart of patterns
        fig_summary = px.bar(
            df_summary,
            x="company_count",
            y="pattern",
            orientation="h",
            color="pattern",
            labels={"company_count": "Number of Companies", "pattern": "Allocation Strategy"},
            color_discrete_sequence=px.colors.qualitative.Dark24,
            title=f"Latest Capital Allocation Pattern Distribution ({df_summary['latest_year'].iloc[0]})"
        )
        fig_summary.update_layout(
            showlegend=False,
            margin=dict(t=40, l=10, r=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff', family="Inter"),
            height=350
        )
        st.plotly_chart(fig_summary, use_container_width=True)
    else:
        st.info("Allocation distribution summary not found. Please run the ETL pipeline first.")
        
    st.markdown("---")
    st.subheader("🔄 Year-over-Year Strategy Shifts")
    
    if changes_path.exists():
        df_changes = pd.read_csv(changes_path)
        
        # Setup sidebar/filter elements in layout
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            cats = ["All Changes"] + sorted(list(df_changes["change_category"].unique()))
            sel_cat = st.selectbox("Filter by Transition Type:", cats)
        with col_f2:
            years = ["All Years"] + sorted(list(df_changes["year"].astype(str).unique()), reverse=True)
            sel_yr = st.selectbox("Filter by Transition Year:", years)
        with col_f3:
            search_query = st.text_input("Search Company ID / Name:")
            
        # Apply filters
        df_changes_filt = df_changes.copy()
        if sel_cat != "All Changes":
            df_changes_filt = df_changes_filt[df_changes_filt["change_category"] == sel_cat]
        if sel_yr != "All Years":
            df_changes_filt = df_changes_filt[df_changes_filt["year"] == sel_yr]
        if search_query:
            q = search_query.strip().lower()
            df_changes_filt = df_changes_filt[
                df_changes_filt["company_id"].str.lower().str.contains(q) |
                df_changes_filt["company_name"].str.lower().str.contains(q)
            ]
            
        st.markdown(f"**Found {len(df_changes_filt)} transition events matching criteria.**")
        
        # Format table for presentation
        df_changes_table = df_changes_filt.copy()
        df_changes_table.rename(columns={
            "company_id": "Ticker",
            "company_name": "Company Name",
            "year": "Transition Year",
            "previous_pattern": "Previous Strategy",
            "current_pattern": "Current Strategy",
            "change_category": "Transition Category"
        }, inplace=True)
        
        st.dataframe(
            df_changes_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ticker": st.column_config.TextColumn("Ticker"),
                "Company Name": st.column_config.TextColumn("Company Name"),
                "Transition Year": st.column_config.TextColumn("Transition Year"),
                "Previous Strategy": st.column_config.TextColumn("Previous Strategy"),
                "Current Strategy": st.column_config.TextColumn("Current Strategy"),
                "Transition Category": st.column_config.TextColumn("Transition Category")
            }
        )
    else:
        st.info("No strategy transition changes CSV dataset found.")
