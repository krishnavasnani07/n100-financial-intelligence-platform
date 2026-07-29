import plotly.express as px
import streamlit as st
import pandas as pd

def render_sector_bubble_chart(df: pd.DataFrame, sector_name: str):
    """
    Renders a bubble chart for the selected sector.
    X-axis: Revenue (sales)
    Y-axis: ROE (%)
    Bubble Size: Index Weight (%) as a proxy for Market Cap
    Color: Sub-sector
    """
    if df.empty:
        st.warning(f"No company records found in the {sector_name} sector.")
        return

    # Create a copy to prevent warnings
    df_plot = df.copy()

    # Fill missing values and ensure size is positive
    df_plot['index_weight_pct'] = df_plot['index_weight_pct'].fillna(0.1)
    df_plot['bubble_size'] = df_plot['index_weight_pct'].apply(lambda x: max(float(x), 0.05))

    # Format values for labels
    df_plot['Sales (Cr)'] = df_plot['sales'].apply(lambda x: f"₹{x:,.2f} Cr" if pd.notnull(x) else "N/A")
    df_plot['ROE (%)'] = df_plot['return_on_equity_pct'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
    df_plot['Index Weight (%)'] = df_plot['index_weight_pct'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")

    fig = px.scatter(
        df_plot,
        x="sales",
        y="return_on_equity_pct",
        size="bubble_size",
        color="sub_sector",
        hover_name="company_name",
        hover_data={
            "company_id": True,
            "Sales (Cr)": True,
            "ROE (%)": True,
            "Index Weight (%)": True,
            "sales": False,
            "return_on_equity_pct": False,
            "bubble_size": False
        },
        labels={
            "sales": "Revenue (INR Cr)",
            "return_on_equity_pct": "Return on Equity (ROE %)",
            "sub_sector": "Sub-Sector"
        },
        title=f"Sector Mapping: {sector_name} (Bubble Size: Index Weight %)",
        color_discrete_sequence=px.colors.qualitative.Bold
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.1)',
            title="Revenue (INR Cr)"
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.1)',
            title="Return on Equity (ROE %)"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="center",
            x=0.5
        ),
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)
