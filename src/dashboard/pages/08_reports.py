import pandas as pd
import streamlit as st

from src.dashboard.components.report_links import render_report_links_table
from src.dashboard.utils import db

st.markdown(
    "<h1 style='font-weight:800;'>📄 Annual Reports Browser</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#8892b0; margin-top:-15px;'>Search and view PDF annual reports and BSE corporate filings for Nifty 100 constituents.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")


# Load documents and company master lists
@st.cache_data(ttl=600)
def get_cached_report_data():
    """Get cached report data."""
    try:
        df_docs = db.get_documents()
        df_companies = db.get_companies()
        df = pd.merge(
            df_docs,
            df_companies[["id", "company_name"]],
            left_on="company_id",
            right_on="id",
            how="left",
        )
        return df
    except Exception as e:
        st.error(f"Error loading annual reports data: {e}")
        return pd.DataFrame()


df_docs_all = get_cached_report_data()

if df_docs_all.empty:
    st.warning("No annual report documents found in the database.")
    st.stop()

# Sidebar Filters
st.sidebar.markdown(
    "<h3 style='margin-bottom:5px; font-weight:700;'>🔎 Report Filters</h3>",
    unsafe_allow_html=True,
)

# 1. Company Filter
company_list = sorted(
    df_docs_all[["company_id", "company_name"]]
        .dropna()
        .drop_duplicates()
        .apply(lambda r: f"{r['company_id']} - {r['company_name']}", axis=1)
        .tolist()
)
company_options = ["All Companies"] + company_list
selected_company = st.sidebar.selectbox("Filter by Company:", company_options)

# 2. Year Filter
years_list = sorted(df_docs_all["year"].dropna().unique(), reverse=True)
selected_years = st.sidebar.multiselect(
    "Filter by Financial Year:", options=years_list, default=[]
)

# 3. Availability Filter
availability_option = st.sidebar.radio(
    "Report Availability:",
    options=["All Reports", "Available Only", "Unavailable Only"],
)

# Apply filters
df_filtered = df_docs_all.copy()

# Filter by Company
if selected_company != "All Companies":
    ticker = selected_company.split(" - ")[0].strip()
    df_filtered = df_filtered[df_filtered["company_id"] == ticker]

# Filter by Year
if selected_years:
    df_filtered = df_filtered[df_filtered["year"].isin(selected_years)]

# Classify availability
df_filtered["is_available"] = df_filtered["annual_report"].apply(
    lambda x: pd.notnull(x) and str(x).strip().startswith(("http://", "https://"))
)

# Filter by Availability
if availability_option == "Available Only":
    df_filtered = df_filtered[df_filtered["is_available"] == True]
elif availability_option == "Unavailable Only":
    df_filtered = df_filtered[df_filtered["is_available"] == False]

# Show Result Count
num_reports = len(df_filtered)
st.markdown(f"### 📁 Found {num_reports} report(s)")

# Render report links table
render_report_links_table(df_filtered)
