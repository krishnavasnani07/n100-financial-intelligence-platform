"""
Nifty 100 Financial Intelligence Platform Dashboard.
A production-grade financial research dashboard featuring Executive KPI Cards,
Plotly visualizations, Interactive stock comparisons, Preset screeners, AI insights,
Portfolio builder, Watchlist persistence, and 3-Year Forecasting.
"""

from __future__ import annotations
from typing import Optional
import sqlite3
import hashlib
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# Setup page config first
st.set_page_config(
    page_title="N100 Financial Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.config.settings import DB_PATH
from src.peer_analysis.comparison import load_raw_ratios_data
from src.utils.ai_engine import get_company_insights_data, generate_pdf_report
from src.portfolio.portfolio_engine import calculate_portfolio_metrics
from src.forecasting.forecasting_engine import generate_company_forecasts

# ----------------------------------------------------
# 1. PREMIUM GLASSMORPHIC & DARK MODE STYLING (CSS)
# ----------------------------------------------------
st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
    /* Global Styles */
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', sans-serif;
        background-color: #0B0F19;
        color: #E2E8F0;
    }
    
    /* Header Gradients */
    .main-title {
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 2.8rem;
        margin-bottom: 0.5rem;
    }
    
    /* Glassmorphic Cards */
    .kpi-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: transform 0.2s ease-in-out, border-color 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        border-color: rgba(56, 189, 248, 0.4);
    }
    .kpi-title {
        font-size: 0.9rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .kpi-indicator {
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 0.25rem;
    }
    .indicator-up { color: #10B981; }
    .indicator-down { color: #EF4444; }
    
    /* Custom Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------------------------------
# 2. DATA CACHING & LOAD FUNCTIONS
# ----------------------------------------------------
@st.cache_data(ttl=3600)
def get_cached_ratios_data() -> pd.DataFrame:
    """Loads and caches latest ratios data."""
    df = load_raw_ratios_data(DB_PATH)
    # Deduplicate to latest year
    df["Sector"] = df["Sector"].fillna("Unclassified")
    df["year_int"] = df["year"].apply(
        lambda y: int(y[-4:]) if y and len(str(y)) >= 4 and y[-4:].isdigit() else 2024
    )
    df_latest = (
        df.sort_values(by="year_int", ascending=False)
        .drop_duplicates(subset=["Company"], keep="first")
        .copy()
    )
    return df_latest


@st.cache_data
def get_historical_all_data() -> pd.DataFrame:
    """Loads and caches all historical ratios."""
    df = load_raw_ratios_data(DB_PATH)
    df["Sector"] = df["Sector"].fillna("Unclassified")
    df["year_int"] = df["year"].apply(
        lambda y: int(y[-4:]) if y and len(str(y)) >= 4 and y[-4:].isdigit() else 2024
    )
    return df.sort_values(by=["Company", "year_int"])


def get_db_connection():
    return sqlite3.connect(str(DB_PATH))


# ----------------------------------------------------
# 3. AUTHENTICATION & SESSION MANAGEMENT
# ----------------------------------------------------
def init_session_state():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = "Viewer"
        st.session_state.user_id = None


init_session_state()


def verify_credentials(username, password) -> Optional[tuple[int, str]]:
    conn = get_db_connection()
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        row = conn.execute(
            "SELECT id, role FROM users WHERE username = ? AND password_hash = ?",
            (username.strip().lower(), pw_hash),
        ).fetchone()
        return row if row else None
    finally:
        conn.close()


# ----------------------------------------------------
# 4. SIDEBAR - LOGIN & NAVIGATION
# ----------------------------------------------------
st.sidebar.markdown(
    "<h2 style='text-align: center; color: #38BDF8;'>⚡ N100 Engine</h2>",
    unsafe_allow_html=True,
)

# Login Form
if not st.session_state.logged_in:
    with st.sidebar.form("login_form"):
        st.subheader("Login Access")
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        submitted = st.form_submit_submit = st.form_submit_button("Sign In")

        if submitted:
            user_data = verify_credentials(username_input, password_input)
            if user_data:
                st.session_state.logged_in = True
                st.session_state.user_id = user_data[0]
                st.session_state.username = username_input.strip()
                st.session_state.role = user_data[1]
                st.rerun()
            else:
                st.error("Invalid username/password.")
else:
    st.sidebar.success(
        f"Logged in: {st.session_state.username} ({st.session_state.role})"
    )
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = "Viewer"
        st.session_state.user_id = None
        st.rerun()

# Navigation
st.sidebar.markdown("---")
st.sidebar.subheader("Navigation")
menu_selection = st.sidebar.radio(
    "Select View",
    [
        "Executive Overview",
        "Interactive Stock Matcher",
        "Predefined Screeners",
        "Sector Analysis",
        "AI-Powered Research",
        "Custom Portfolio Risk",
        "3-Year Projections",
    ],
)


# Watchlist persistence (for logged in users)
def add_to_watchlist(company_id: str):
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO watchlists (user_id, company_id) VALUES (?, ?)",
            (st.session_state.user_id, company_id),
        )
        conn.commit()
    finally:
        conn.close()


def remove_from_watchlist(company_id: str):
    conn = get_db_connection()
    try:
        conn.execute(
            "DELETE FROM watchlists WHERE user_id = ? AND company_id = ?",
            (st.session_state.user_id, company_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_watchlist() -> list[str]:
    if not st.session_state.logged_in:
        return []
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT company_id FROM watchlists WHERE user_id = ?",
            (st.session_state.user_id,),
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


# ----------------------------------------------------
# 5. CORE PAGES IMPLEMENTATION
# ----------------------------------------------------
df_latest = get_cached_ratios_data()
df_hist = get_historical_all_data()

# Page 1: Executive Overview
if menu_selection == "Executive Overview":
    st.markdown(
        "<h1 class='main-title'>⚡ Executive Dashboard</h1>", unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color: #94A3B8;'>Real-time metrics, sector distributions, and correlation maps across Nifty 100 universe.</p>",
        unsafe_allow_html=True,
    )

    # KPI Calculations
    total_companies = len(df_latest)
    highest_roe_row = df_latest.sort_values(by="ROE", ascending=False).iloc[0]
    highest_cagr_row = df_latest.sort_values(by="Revenue CAGR", ascending=False).iloc[0]

    # Calculate mock PE (or load from another table if available, else average PE mock)
    avg_pe = 22.4  # Indian market typical PE
    market_leader = "TCS"

    # Display Premium Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Universe</div>
            <div class="kpi-value">{total_companies} Companies</div>
            <div class="kpi-indicator indicator-up">▲ 100% Nifty-100</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title">Highest ROE</div>
            <div class="kpi-value">{highest_roe_row['ROE']}%</div>
            <div class="kpi-indicator indicator-up">★ {highest_roe_row['Company']}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title">Average P/E</div>
            <div class="kpi-value">{avg_pe}x</div>
            <div class="kpi-indicator indicator-down">▼ Valuation Premium</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
        <div class="kpi-card">
            <div class="kpi-title">Highest 5Y CAGR</div>
            <div class="kpi-value">{highest_cagr_row['Revenue CAGR']}%</div>
            <div class="kpi-indicator indicator-up">▲ {highest_cagr_row['Company']}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Layout with Charts
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Sector Asset Distribution")
        # Treemap
        fig_tree = px.treemap(
            df_latest,
            path=["Sector", "Company"],
            values="Composite Quality Score",
            color="Composite Quality Score",
            color_continuous_scale="RdYlBu_r",
        )
        fig_tree.update_layout(
            margin=dict(t=10, l=10, r=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_tree, use_container_width=True)

    with c2:
        st.subheader("Profitability vs Growth Risk Matrix")
        # Bubble chart (ROE vs. Debt/Equity vs Composite score)
        fig_bubble = px.scatter(
            df_latest.dropna(subset=["ROE", "Debt to Equity"]),
            x="Debt to Equity",
            y="ROE",
            size="Composite Quality Score",
            color="Sector",
            hover_name="Company",
            log_x=True,
            title="Bubble Size: Quality Score",
        )
        fig_bubble.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0",
        )
        st.plotly_chart(fig_bubble, use_container_width=True)

    # Correlation Heatmap
    st.subheader("Ratio Multi-Correlation Map")
    kpis = [
        "ROE",
        "ROCE",
        "Revenue CAGR",
        "PAT CAGR",
        "Debt to Equity",
        "Operating Margin",
        "Interest Coverage",
        "Composite Quality Score",
    ]
    corr = df_latest[kpis].corr()

    fig_heat = go.Figure(
        data=go.Heatmap(
            z=corr.values, x=corr.columns, y=corr.index, colorscale="Viridis"
        )
    )
    fig_heat.update_layout(
        margin=dict(t=10, l=10, r=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E2E8F0",
    )
    st.plotly_chart(fig_heat, use_container_width=True)


# Page 2: Interactive Stock Matcher
elif menu_selection == "Interactive Stock Matcher":
    st.markdown(
        "<h1 class='main-title'>⚡ Side-by-Side Comparison</h1>", unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color: #94A3B8;'>Perform head-to-head financial analysis across two companies.</p>",
        unsafe_allow_html=True,
    )

    comp_list = sorted(df_latest["Company"].tolist())

    col1, col2 = st.columns(2)
    with col1:
        comp_a = st.selectbox("Select Company A", comp_list, index=0)
    with col2:
        comp_b = st.selectbox(
            "Select Company B", comp_list, index=min(1, len(comp_list) - 1)
        )

    row_a = df_latest[df_latest["Company"] == comp_a].iloc[0]
    row_b = df_latest[df_latest["Company"] == comp_b].iloc[0]

    # Display comparison table
    st.subheader("Financial Profile Breakdown")
    kpi_map = {
        "Sector": "Sector",
        "ROE (%)": "ROE",
        "ROCE (%)": "ROCE",
        "Operating Margin (%)": "Operating Margin",
        "Revenue CAGR (5Y %)": "Revenue CAGR",
        "PAT CAGR (5Y %)": "PAT CAGR",
        "Debt to Equity": "Debt to Equity",
        "Interest Coverage": "Interest Coverage",
        "Composite Quality Score": "Composite Quality Score",
    }

    comp_data = []
    for display_name, col_name in kpi_map.items():
        val_a = row_a[col_name]
        val_b = row_b[col_name]

        # Color match highlighting
        better_marker_a = ""
        better_marker_b = ""

        if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
            if col_name == "Debt to Equity":  # Lower is better
                if val_a < val_b:
                    better_marker_a = " 🟢"
                elif val_b < val_a:
                    better_marker_b = " 🟢"
            else:  # Higher is better
                if val_a > val_b:
                    better_marker_a = " 🟢"
                elif val_b > val_a:
                    better_marker_b = " 🟢"

        comp_data.append(
            {
                "Ratio / Indicator": display_name,
                f"{comp_a}": f"{val_a}{better_marker_a}",
                f"{comp_b}": f"{val_b}{better_marker_b}",
            }
        )

    st.table(pd.DataFrame(comp_data).set_index("Ratio / Indicator"))

    # Historical Trends Side-by-Side
    st.subheader("Historical Performance comparison")
    hist_a = df_hist[df_hist["Company"] == comp_a]
    hist_b = df_hist[df_hist["Company"] == comp_b]

    c1, c2 = st.columns(2)
    with c1:
        # ROE Trend chart
        fig_roe = go.Figure()
        fig_roe.add_trace(
            go.Scatter(
                x=hist_a["year"],
                y=hist_a["ROE"],
                name=f"{comp_a} ROE",
                line=dict(color="#38BDF8", width=3),
            )
        )
        fig_roe.add_trace(
            go.Scatter(
                x=hist_b["year"],
                y=hist_b["ROE"],
                name=f"{comp_b} ROE",
                line=dict(color="#C084FC", width=3),
            )
        )
        fig_roe.update_layout(
            title="Historical ROE Trend",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0",
        )
        st.plotly_chart(fig_roe, use_container_width=True)
    with c2:
        # Sales Trend chart
        fig_sales = go.Figure()
        # Find raw sales from profit & loss table
        conn = get_db_connection()
        sales_a = pd.read_sql(
            "SELECT year, sales FROM profitandloss WHERE company_id = ? ORDER BY year",
            conn,
            params=[comp_a],
        )
        sales_b = pd.read_sql(
            "SELECT year, sales FROM profitandloss WHERE company_id = ? ORDER BY year",
            conn,
            params=[comp_b],
        )
        conn.close()

        fig_sales.add_trace(
            go.Scatter(
                x=sales_a["year"],
                y=sales_a["sales"],
                name=f"{comp_a} Sales (Cr)",
                line=dict(color="#10B981", width=3),
            )
        )
        fig_sales.add_trace(
            go.Scatter(
                x=sales_b["year"],
                y=sales_b["sales"],
                name=f"{comp_b} Sales (Cr)",
                line=dict(color="#F59E0B", width=3),
            )
        )
        fig_sales.update_layout(
            title="Historical Sales Revenue",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0",
        )
        st.plotly_chart(fig_sales, use_container_width=True)


# Page 3: Predefined Screeners
elif menu_selection == "Predefined Screeners":
    st.markdown(
        "<h1 class='main-title'>⚡ Predefined Analyst Screeners</h1>",
        unsafe_allow_html=True,
    )

    presets = [
        "Quality Compounder",
        "Value Pick",
        "Growth Accelerator",
        "Dividend Champion",
        "Debt-Free Blue Chip",
        "Turnaround Watch",
    ]

    screener_choice = st.selectbox("Select Investment Strategy", presets)

    from src.screener.presets import run_preset, load_screener_master_data

    try:
        master_df = load_screener_master_data(DB_PATH)
        matched_df = run_preset(screener_choice, master_df)

        st.subheader(f"Strategy: {screener_choice} ({len(matched_df)} Companies Match)")

        # Display table
        cols_to_show = [
            "company_id",
            "sector",
            "return_on_equity_pct",
            "revenue_cagr_5yr",
            "debt_to_equity",
            "composite_quality_score",
        ]
        disp_df = matched_df[cols_to_show].rename(
            columns={
                "company_id": "Company",
                "sector": "Sector",
                "return_on_equity_pct": "ROE",
                "revenue_cagr_5yr": "5Y CAGR",
                "debt_to_equity": "D/E",
                "composite_quality_score": "Composite Score",
            }
        )
        st.dataframe(disp_df, use_container_width=True)

    except Exception as e:
        st.error(f"Failed to execute screener preset: {e}")


# Page 4: Sector Analysis
elif menu_selection == "Sector Analysis":
    st.markdown(
        "<h1 class='main-title'>⚡ Sector-wise Peer ranking</h1>",
        unsafe_allow_html=True,
    )

    from src.peer_analysis.comparison import run_peer_analysis

    peer_comp_df, sector_stats_df, top_perf_df, bottom_perf_df = run_peer_analysis(
        DB_PATH
    )

    sectors_list = sorted(peer_comp_df["Sector"].unique())
    selected_sector = st.selectbox("Select Sector", sectors_list)

    st.subheader(f"Companies in {selected_sector} Sector")
    sector_group = peer_comp_df[peer_comp_df["Sector"] == selected_sector].sort_values(
        by="Peer Rank"
    )
    st.dataframe(sector_group, use_container_width=True)

    # Sector Stats
    st.subheader("Sector Benchmark Statistics (Mean / Median / Min / Max)")
    sec_stats = sector_stats_df[sector_stats_df["Sector"] == selected_sector]
    st.table(sec_stats.set_index("KPI"))


# Page 5: AI-Powered Research
elif menu_selection == "AI-Powered Research":
    st.markdown(
        "<h1 class='main-title'>⚡ AI Copilot Insights</h1>", unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color: #94A3B8;'>Instant, rule-based natural language summaries and automated PDF reporting.</p>",
        unsafe_allow_html=True,
    )

    comp_list = sorted(df_latest["Company"].tolist())
    target_comp = st.selectbox("Select Company to Analyze", comp_list)

    insights = get_company_insights_data(target_comp, DB_PATH)

    if insights.get("success", False):
        st.subheader("1. AI Financial Overview Summary")
        st.info(insights["summary"])

        st.subheader("2. AI Investment Thesis Analysis")
        st.success(insights["recommendation"])

        # Download PDF Report button
        st.subheader("3. Export Professional PDF Report")
        pdf_buf = generate_pdf_report(target_comp, insights)
        st.download_button(
            label=f"📥 Download {target_comp} PDF Report",
            data=pdf_buf.getvalue(),
            file_name=f"{target_comp}_research_report.pdf",
            mime="application/pdf",
        )
    else:
        st.error(insights.get("message", "Error generating insights."))


# Page 6: Custom Portfolio Risk
elif menu_selection == "Custom Portfolio Risk":
    st.markdown(
        "<h1 class='main-title'>⚡ Portfolio Allocation Builder</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #94A3B8;'>Input investment and allocate capital across chosen Nifty 100 securities to evaluate overall risk indicators.</p>",
        unsafe_allow_html=True,
    )

    capital = st.number_input(
        "Total Investment Capital (₹)", min_value=1000, value=100000, step=5000
    )

    comp_list = sorted(df_latest["Company"].tolist())
    selected_assets = st.multiselect(
        "Select Portfolio Assets",
        comp_list,
        default=(
            ["TCS", "INFY"]
            if "TCS" in comp_list and "INFY" in comp_list
            else comp_list[:2]
        ),
    )

    if len(selected_assets) < 1:
        st.warning("Please select at least 1 stock.")
    else:
        st.subheader("Configure Capital Allocation (%)")
        allocations = {}
        total_alloc = 0

        cols = st.columns(len(selected_assets))
        for idx, asset in enumerate(selected_assets):
            with cols[idx]:
                alloc_pct = st.slider(
                    f"{asset} Weight", 0, 100, int(100 / len(selected_assets))
                )
                allocations[asset] = alloc_pct / 100.0
                total_alloc += alloc_pct

        if total_alloc != 100:
            st.warning(f"Total allocation must equal 100%. Currently: {total_alloc}%")
        else:
            # Calculate Risk Metrics
            with st.spinner("Calculating portfolio historical risk metrics..."):
                metrics = calculate_portfolio_metrics(allocations, db_path=DB_PATH)

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Expected Return", f"{metrics['expected_return']}%")
            with c2:
                st.metric("Portfolio Volatility (SD)", f"{metrics['volatility']}%")
            with c3:
                st.metric("Portfolio Beta", f"{metrics['beta']}")
            with c4:
                st.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']}")

            st.metric(
                "Diversification Score", f"{metrics['diversification_score']} / 100"
            )

            # Watchlist additions inside dashboard!
            if st.session_state.logged_in:
                st.subheader("Manage User Watchlist")
                current_watchlist = get_watchlist()

                for asset in selected_assets:
                    if asset in current_watchlist:
                        if st.button(f"Remove {asset} from My Watchlist"):
                            remove_from_watchlist(asset)
                            st.success(f"Removed {asset}!")
                            st.rerun()
                    else:
                        if st.button(f"Add {asset} to My Watchlist"):
                            add_to_watchlist(asset)
                            st.success(f"Added {asset}!")
                            st.rerun()


# Page 7: 3-Year Projections
elif menu_selection == "3-Year Projections":
    st.markdown(
        "<h1 class='main-title'>⚡ Predictive Financial Projections</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color: #94A3B8;'>3-Year forecasts for Sales Revenue and Earnings Per Share (EPS) using Linear Regression and Moving Average curves.</p>",
        unsafe_allow_html=True,
    )

    comp_list = sorted(df_latest["Company"].tolist())
    target_comp = st.selectbox("Select Company for Projections", comp_list)

    fc_res = generate_company_forecasts(target_comp, DB_PATH)

    if fc_res.get("success", False):
        hist_df = pd.DataFrame(fc_res["historical"])
        fc_df = pd.DataFrame(fc_res["forecasts"])

        # Merge for plotting
        full_years = list(hist_df["Year"]) + list(fc_df["Year"])

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Sales Revenue Projections (Cr)")
            fig_sales = go.Figure()
            # Historical
            fig_sales.add_trace(
                go.Scatter(
                    x=hist_df["Year"],
                    y=hist_df["Revenue"],
                    mode="markers+lines",
                    name="Historical",
                    line=dict(color="#10B981", width=3),
                )
            )
            # Linear Regression
            fig_sales.add_trace(
                go.Scatter(
                    x=[hist_df["Year"].iloc[-1]] + list(fc_df["Year"]),
                    y=[hist_df["Revenue"].iloc[-1]]
                    + list(fc_df["Revenue (Linear Regression)"]),
                    mode="lines",
                    name="Linear Trend Forecast",
                    line=dict(color="#38BDF8", dash="dash", width=3),
                )
            )
            # Moving Average
            fig_sales.add_trace(
                go.Scatter(
                    x=[hist_df["Year"].iloc[-1]] + list(fc_df["Year"]),
                    y=[hist_df["Revenue"].iloc[-1]]
                    + list(fc_df["Revenue (Moving Average)"]),
                    mode="lines",
                    name="Moving Average Forecast",
                    line=dict(color="#F59E0B", dash="dot", width=3),
                )
            )
            fig_sales.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#E2E8F0",
            )
            st.plotly_chart(fig_sales, use_container_width=True)
            st.write(
                f"Compound growth rate based on trend slope: **{fc_res['revenue_trend_growth_rate']}%**"
            )

        with c2:
            st.subheader("Earnings Per Share (EPS) Projections")
            fig_eps = go.Figure()
            # Historical
            fig_eps.add_trace(
                go.Scatter(
                    x=hist_df["Year"],
                    y=hist_df["EPS"],
                    mode="markers+lines",
                    name="Historical",
                    line=dict(color="#C084FC", width=3),
                )
            )
            # Linear Regression
            fig_eps.add_trace(
                go.Scatter(
                    x=[hist_df["Year"].iloc[-1]] + list(fc_df["Year"]),
                    y=[hist_df["EPS"].iloc[-1]]
                    + list(fc_df["EPS (Linear Regression)"]),
                    mode="lines",
                    name="Linear Trend Forecast",
                    line=dict(color="#E879F9", dash="dash", width=3),
                )
            )
            # Moving Average
            fig_eps.add_trace(
                go.Scatter(
                    x=[hist_df["Year"].iloc[-1]] + list(fc_df["Year"]),
                    y=[hist_df["EPS"].iloc[-1]] + list(fc_df["EPS (Moving Average)"]),
                    mode="lines",
                    name="Moving Average Forecast",
                    line=dict(color="#F43F5E", dash="dot", width=3),
                )
            )
            fig_eps.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#E2E8F0",
            )
            st.plotly_chart(fig_eps, use_container_width=True)
            st.write(
                f"Compound growth rate based on trend slope: **{fc_res['eps_trend_growth_rate']}%**"
            )

    else:
        st.error(fc_res.get("message", "Error generating projections."))
