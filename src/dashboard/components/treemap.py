import pandas as pd
import plotly.express as px
import streamlit as st


def classify_company_capital_allocation(row: pd.Series) -> str:
    """
    Classifies a company into a single capital allocation category based on hierarchical rules.
    """
    de = row.get("debt_to_equity")
    roe = row.get("return_on_equity_pct")
    rev_cagr_5 = row.get("revenue_cagr_5yr")
    capex = row.get("capex_cr")
    sales = row.get("sales")
    div_yield = row.get("dividend_yield")
    payout = row.get("dividend_payout_ratio_pct")
    pe = row.get("pe")
    fcf = row.get("free_cash_flow_cr")
    rev_cagr_3 = row.get("revenue_cagr_3yr")

    # 1. Debt-Free: strictly zero debt
    if pd.notnull(de) and de == 0:
        return "Debt-Free"

    # 2. Capital Efficient: ROE > 20% and low leverage
    if pd.notnull(roe) and roe > 20.0 and pd.notnull(de) and de < 0.5:
        return "Capital Efficient"

    # 3. Growth Focused: 5y Revenue growth > 15% and positive capital expenditure
    if pd.notnull(rev_cagr_5) and rev_cagr_5 > 15.0 and pd.notnull(capex) and capex > 0:
        return "Growth Focused"

    # 4. Dividend Leaders: high dividend yield or payout ratio
    if (pd.notnull(div_yield) and div_yield > 2.0) or (
        pd.notnull(payout) and payout > 30.0
    ):
        return "Dividend Leaders"

    # 5. High Capex: Capex is more than 10% of revenue
    if pd.notnull(capex) and pd.notnull(sales) and sales > 0 and (capex / sales) > 0.10:
        return "High Capex"

    # 6. Value: low price-to-earnings ratio
    if pd.notnull(pe) and 0 < pe < 15.0:
        return "Value"

    # 7. Turnaround: FCF positive and solid short-term revenue CAGR
    if pd.notnull(fcf) and fcf > 0 and pd.notnull(rev_cagr_3) and rev_cagr_3 > 10.0:
        return "Turnaround"

    # Default category
    return "Balanced"


def render_capital_allocation_treemap(df: pd.DataFrame):
    """
    Renders an interactive Plotly Treemap.
    """
    if df.empty:
        st.warning("No data available to display the Capital Allocation map.")
        return

    # Create copy and prepare columns
    df_plot = df.copy()

    # Fill missing index weights and prepare size
    df_plot["index_weight_pct"] = df_plot["index_weight_pct"].fillna(0.1)
    df_plot["block_size"] = df_plot["index_weight_pct"].apply(
        lambda x: max(float(x), 0.05)
    )

    # Add custom formatting for details
    df_plot["ROE (%)"] = df_plot["return_on_equity_pct"].apply(
        lambda x: f"{x:.1f}%" if pd.notnull(x) else "N/A"
    )
    df_plot["D/E (x)"] = df_plot["debt_to_equity"].apply(
        lambda x: f"{x:.2f}x" if pd.notnull(x) else "N/A"
    )
    df_plot["Composite Score"] = df_plot["composite_quality_score"].apply(
        lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A"
    )

    fig = px.treemap(
        df_plot,
        path=["category", "company_name"],
        values="block_size",
        color="category",
        hover_data={
            "company_id": True,
            "Composite Score": True,
            "ROE (%)": True,
            "D/E (x)": True,
            "block_size": False,
        },
        title="Capital Allocation Map (Hierarchical Categories, size: Index Weight %)",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )

    fig.update_layout(
        margin=dict(t=40, l=10, r=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ffffff", family="Inter"),
        height=550,
    )

    st.plotly_chart(fig, use_container_width=True)
