import streamlit as st
import pandas as pd
from src.dashboard.components.radar import load_radar_universe_data, calculate_normalized_radar_metrics, render_peer_radar
from src.dashboard.components.peer_table import render_peer_table

st.markdown("<h1 style='font-weight:800;'>👥 Peer Comparison</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#8892b0; margin-top:-15px;'>Compare a company's financial strength and quality metrics directly with its sector peers.</p>", unsafe_allow_html=True)
st.markdown("---")

# Load raw and normalized master data
@st.cache_data(ttl=600)
def get_cached_radar_data():
    df_raw = load_radar_universe_data()
    df_norm = calculate_normalized_radar_metrics(df_raw)
    return df_raw, df_norm

df_raw, df_norm = get_cached_radar_data()

if df_raw.empty:
    st.warning("Database contains no data or could not be loaded.")
    st.stop()

# Sidebar Sector & Company Selection
st.sidebar.markdown("<h3 style='margin-bottom:5px; font-weight:700;'>👥 Peer Selector</h3>", unsafe_allow_html=True)

# Sector selector
sectors_list = sorted(list(df_raw['sector'].dropna().unique()))
selected_sector = st.sidebar.selectbox("Select Broad Sector:", sectors_list)

# Filter companies by sector
df_sector_companies = df_raw[df_raw['sector'] == selected_sector]

# Company selector (updates based on sector)
company_options = [f"{row['company_id']} - {row['company_name']}" for _, row in df_sector_companies.iterrows()]
company_options.sort()

selected_option = st.sidebar.selectbox("Select Target Company:", company_options)

if not selected_option:
    st.info("Please select a company to perform peer analysis.")
    st.stop()

selected_company_id = selected_option.split(" - ")[0].strip()

# Main Layout
col_radar, col_table = st.columns([1, 1])

with col_radar:
    st.subheader("Financial Health Profile")
    st.markdown("*Shows winsorized 0-100 normalized scores (outer bounds indicate top decile performance)*")
    render_peer_radar(selected_company_id, df_raw, df_norm)

with col_table:
    render_peer_table(df_sector_companies, selected_company_id)
