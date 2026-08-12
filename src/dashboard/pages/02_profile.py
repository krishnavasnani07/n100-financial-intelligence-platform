import pandas as pd
import streamlit as st

from src.dashboard.components.cards import kpi_card
from src.dashboard.components.charts import (
    render_profit_chart,
    render_revenue_chart,
    render_roe_roce_trend,
)
from src.dashboard.utils import db
from src.dashboard.utils.helpers import extract_year_int

st.title("🏢 Company Profile")

# Load master lists for company auto-complete search
try:
    df_companies = db.get_companies()
    df_sectors = db.get_sectors()
except Exception:
    st.error("Unable to load data. Please build the database first.")
    st.stop()

if df_companies.empty:
    st.warning("No company records found in the database.")
    st.stop()

# Search box combining ticker and company name
company_options = [
    f"{row['id']} - {row['company_name']}" for _, row in df_companies.iterrows()
]
selected_option = st.selectbox("Search Company by Name or NSE Ticker:", company_options)

if not selected_option:
    st.info("Search and select a company to display the profile.")
    st.stop()

# Extract ticker from option
selected_ticker = selected_option.split(" - ")[0].strip()

# Verification check
if selected_ticker not in df_companies["id"].values:
    st.error("Ticker not found. Please search another company.")
    st.stop()

# Fetch company profile details
company_info = df_companies[df_companies["id"] == selected_ticker].iloc[0]
sector_info = df_sectors[df_sectors["company_id"] == selected_ticker]

sector_name = sector_info.iloc[0]["broad_sector"] if not sector_info.empty else "N/A"
sub_sector_name = sector_info.iloc[0]["sub_sector"] if not sector_info.empty else "N/A"

# 1. Company Card layout
with st.container():
    col_logo, col_desc = st.columns([1, 4])
    with col_logo:
        logo_url = company_info.get("company_logo")
        # Display logo if URL is available, otherwise use a clean styled placeholder icon
        if logo_url and pd.notnull(logo_url) and len(str(logo_url)) > 0:
            st.image(logo_url, width=120)
        else:
            st.markdown(
                "<div style='background-color: rgba(118, 75, 162, 0.1); border-radius: 12px; height: 120px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(118, 75, 162, 0.3);'>"
                "<span style='font-size: 3rem;'>🏢</span></div>",
                unsafe_allow_html=True,
            )
    with col_desc:
        st.markdown(
            f"<h2 style='margin-bottom: 2px; font-weight: 700;'>{company_info['company_name']}</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"**NSE Ticker:** `{selected_ticker}` | **Sector:** {sector_name} | **Sub-Sector:** {sub_sector_name}"
        )
        st.markdown(
            company_info.get("about_company")
            or "No description available for this company."
        )

st.markdown("---")

# Fetch and prep financial records
df_ratios_all = db.get_ratios()
df_company_ratios = df_ratios_all[df_ratios_all["company_id"] == selected_ticker].copy()
df_company_ratios["year_int"] = df_company_ratios["year"].apply(extract_year_int)

df_pl_all = db.get_pl()
df_company_pl = df_pl_all[df_pl_all["company_id"] == selected_ticker].copy()
df_company_pl["year_int"] = df_company_pl["year"].apply(extract_year_int)

if df_company_ratios.empty:
    st.warning("No financial records found for the selected company.")
    st.stop()

# Sort to find the latest financial year record
df_company_ratios_sorted = df_company_ratios.sort_values(by="year_int", ascending=False)
latest_ratios = df_company_ratios_sorted.iloc[0]

# 2. Render Financial Metric Cards
st.subheader(f"Latest Key Financial Indicators ({latest_ratios['year']})")
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    roe = latest_ratios.get("return_on_equity_pct")
    kpi_card(
        "ROE",
        f"{roe:.2f}%" if pd.notnull(roe) else "N/A",
        "Return on Equity",
        (
            "positive"
            if (roe or 0) >= 20.0
            else ("neutral" if (roe or 0) >= 12.0 else "negative")
        ),
    )
with col2:
    roce = latest_ratios.get("return_on_capital_employed_pct")
    kpi_card(
        "ROCE",
        f"{roce:.2f}%" if pd.notnull(roce) else "N/A",
        "Return on Capital",
        (
            "positive"
            if (roce or 0) >= 20.0
            else ("neutral" if (roce or 0) >= 12.0 else "negative")
        ),
    )
with col3:
    npm = latest_ratios.get("net_profit_margin_pct")
    kpi_card(
        "Net Profit Margin",
        f"{npm:.2f}%" if pd.notnull(npm) else "N/A",
        "Net Margin",
        (
            "positive"
            if (npm or 0) >= 15.0
            else ("neutral" if (npm or 0) >= 8.0 else "negative")
        ),
    )
with col4:
    rev_cagr = latest_ratios.get("revenue_cagr_5yr")
    kpi_card(
        "Revenue CAGR (5y)",
        f"{rev_cagr:.2f}%" if pd.notnull(rev_cagr) else "N/A",
        "5-Year Revenue Growth",
        (
            "positive"
            if (rev_cagr or 0) >= 12.0
            else ("neutral" if (rev_cagr or 0) >= 6.0 else "negative")
        ),
    )
with col5:
    de = latest_ratios.get("debt_to_equity")
    kpi_card(
        "Debt to Equity",
        f"{de:.2f}x" if pd.notnull(de) else "N/A",
        "Leverage Ratio",
        (
            "positive"
            if (de or 99) < 0.5
            else ("neutral" if (de or 0) < 1.5 else "negative")
        ),
    )
with col6:
    fcf = latest_ratios.get("free_cash_flow_cr")
    kpi_card(
        "Latest FCF",
        f"₹{fcf:,.1f} Cr" if pd.notnull(fcf) else "N/A",
        "Free Cash Flow",
        "positive" if (fcf or 0) > 0 else "negative",
    )

st.markdown("---")

# 3. Financial Charts
col_charts_left, col_charts_right = st.columns(2)

with col_charts_left:
    st.subheader("Historical Revenue Trend")
    render_revenue_chart(df_company_pl)

with col_charts_right:
    st.subheader("Historical Net Profit Trend")
    render_profit_chart(df_company_pl)

st.subheader("ROE vs ROCE Trend")
render_roe_roce_trend(df_company_ratios)

st.markdown("---")

# 4. Generate Rule-Based Pros & Cons
pros = []
cons = []

# ROE check
roe_val = latest_ratios.get("return_on_equity_pct")
if pd.notnull(roe_val):
    if roe_val >= 20.0:
        pros.append(f"ROE is outstanding at {roe_val:.2f}% (>20%)")
    elif roe_val >= 12.0:
        pros.append(f"ROE is stable at {roe_val:.2f}% (>=12%)")
    else:
        cons.append(f"Weak capital return with ROE at {roe_val:.2f}% (<12%)")

# Debt check
de_val = latest_ratios.get("debt_to_equity")
if pd.notnull(de_val):
    if de_val == 0:
        pros.append("Completely debt-free capital structure")
    elif de_val < 0.5:
        pros.append(f"Conservative borrowing with Debt-to-Equity of {de_val:.2f}x")
    elif de_val > 1.5:
        cons.append(f"High risk leverage with Debt-to-Equity of {de_val:.2f}x")

# YoY Revenue Trend Check
df_pl_sorted = df_company_pl.sort_values(by="year_int")
if len(df_pl_sorted) >= 2:
    latest_rev = df_pl_sorted.iloc[-1].get("sales")
    prev_rev = df_pl_sorted.iloc[-2].get("sales")
    if pd.notnull(latest_rev) and pd.notnull(prev_rev) and prev_rev > 0:
        if latest_rev > prev_rev:
            growth = ((latest_rev - prev_rev) / prev_rev) * 100
            pros.append(
                f"YoY Revenue expansion of {growth:.2f}% (latest vs previous period)"
            )
        else:
            decline = ((prev_rev - latest_rev) / prev_rev) * 100
            cons.append(
                f"YoY Revenue contraction of {decline:.2f}% (latest vs previous period)"
            )

# Free Cash Flow Check
fcf_val = latest_ratios.get("free_cash_flow_cr")
if pd.notnull(fcf_val):
    if fcf_val > 250:
        pros.append(f"Excellent Free Cash Flow pool of ₹{fcf_val:,.1f} Cr")
    elif fcf_val > 0:
        pros.append(f"Positive cash flow generator (FCF: ₹{fcf_val:,.1f} Cr)")
    else:
        cons.append(f"Negative free cash flow pool of ₹{fcf_val:,.1f} Cr")

# Render Pros & Cons badges
col_p, col_c = st.columns(2)
with col_p:
    st.markdown("#### ✅ Strengths")
    if pros:
        for p in pros:
            st.markdown(f'<div class="badge-pros">✅ {p}</div>', unsafe_allow_html=True)
    else:
        st.write("No major strengths identified.")

with col_c:
    st.markdown("#### ❌ Areas of Concern")
    if cons:
        for c in cons:
            st.markdown(f'<div class="badge-cons">❌ {c}</div>', unsafe_allow_html=True)
    else:
        st.write("No major concerns identified.")

st.markdown("---")

# 5. Capital Allocation Strategy Evolution
st.subheader("💰 Capital Allocation Strategy Evolution")
from pathlib import Path

alloc_path = Path("output/capital_allocation.csv")
if alloc_path.exists():
    df_alloc_csv = pd.read_csv(alloc_path)
    df_alloc_csv["company_id"] = (
        df_alloc_csv["company_id"].astype(str).str.strip().str.upper()
    )
    df_comp_alloc = df_alloc_csv[df_alloc_csv["company_id"] == selected_ticker].copy()

    if not df_comp_alloc.empty:
        df_comp_alloc["year_int"] = df_comp_alloc["year"].apply(extract_year_int)
        df_comp_alloc = df_comp_alloc.sort_values(by="year_int", ascending=True)

        latest_alloc = df_comp_alloc.iloc[-1]["pattern_label"]
        st.markdown(f"**Latest Allocation Strategy Status:** `{latest_alloc}`")

        # Display chronological timeline of patterns
        st.markdown("#### 📈 Historical Sequence of Allocation Patterns")
        df_seq = df_comp_alloc[["year", "pattern_label"]].rename(
            columns={"year": "Financial Year", "pattern_label": "Strategy Pattern"}
        )
        st.dataframe(df_seq, use_container_width=True, hide_index=True)

        # Load transitions
        changes_path = Path("output/pattern_changes.csv")
        if changes_path.exists():
            df_changes = pd.read_csv(changes_path)
            df_changes["company_id"] = (
                df_changes["company_id"].astype(str).str.strip().str.upper()
            )
            df_comp_changes = df_changes[
                df_changes["company_id"] == selected_ticker
            ].sort_values(by="year")
            if not df_comp_changes.empty:
                st.markdown("#### 🔄 Transition Events")
                for _, row in df_comp_changes.iterrows():
                    st.markdown(
                        f"🔹 **{row['year']}**: Transitioned from `{row['previous_pattern']}` to `{row['current_pattern']}` (Type: **{row['change_category']}**)"
                    )
            else:
                st.info(
                    "No strategy changes detected over the historical period. Strategy has remained consistent."
                )
else:
    st.info("Capital allocation historical dataset not found.")
