import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render_sector_donut_chart(df: pd.DataFrame):
    """
    Renders a sector distribution donut chart.

    Args:
        df (pd.DataFrame): DataFrame containing companies with sector info.
    """
    # Identify column name for sector
    sector_col = None
    for col in ["sector", "broad_sector", "Sector"]:
        if col in df.columns:
            sector_col = col
            break

    if not sector_col or df.empty:
        st.warning("No sector data available.")
        return

    sector_counts = df[sector_col].value_counts().reset_index()
    sector_counts.columns = ["Sector", "Companies"]

    # Sort and take top sectors if needed, but display nicely
    fig = px.pie(
        sector_counts,
        values="Companies",
        names="Sector",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Bold,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>Companies: %{value}<br>Percentage: %{percent:.1%}<extra></extra>",
    )

    fig.update_layout(
        showlegend=True,
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.5, "xanchor": "center", "x": 0.5},
        margin={"t": 10, "b": 10, "l": 10, "r": 10},
        height=450,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#ffffff", "size": 11},
    )

    st.plotly_chart(fig, use_container_width=True)


def render_revenue_chart(df_pl: pd.DataFrame):
    """
    Plots a 10-year Revenue Bar Chart.

    Args:
        df_pl (pd.DataFrame): DataFrame containing profit and loss history.
    """
    if df_pl.empty:
        st.warning("No financial data available.")
        return

    # Sort chronologically by year_int or year
    if "year_int" in df_pl.columns:
        df_sorted = df_pl.sort_values("year_int")
    else:
        df_sorted = df_pl.sort_values("year")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_sorted["year"],
            y=df_sorted["sales"],
            name="Revenue (Cr)",
            marker_color="#a29bfe",
            hovertemplate="Year: %{x}<br>Revenue: ₹%{y:,.2f} Cr<extra></extra>",
        )
    )

    fig.update_layout(
        margin={"t": 30, "b": 10, "l": 10, "r": 10},
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#ffffff"},
        xaxis={"showgrid": False, "title": "Financial Year"},
        yaxis={
            "showgrid": True,
            "gridcolor": "rgba(255, 255, 255, 0.1)",
            "title": "Revenue (INR Cr)",
        },
    )

    st.plotly_chart(fig, use_container_width=True)


def render_profit_chart(df_pl: pd.DataFrame):
    """
    Plots a 10-year Net Profit Bar Chart.

    Args:
        df_pl (pd.DataFrame): DataFrame containing profit and loss history.
    """
    if df_pl.empty:
        st.warning("No financial data available.")
        return

    if "year_int" in df_pl.columns:
        df_sorted = df_pl.sort_values("year_int")
    else:
        df_sorted = df_pl.sort_values("year")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=df_sorted["year"],
            y=df_sorted["net_profit"],
            name="Net Profit (Cr)",
            marker_color="#00b894",
            hovertemplate="Year: %{x}<br>Net Profit: ₹%{y:,.2f} Cr<extra></extra>",
        )
    )

    fig.update_layout(
        margin={"t": 30, "b": 10, "l": 10, "r": 10},
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#ffffff"},
        xaxis={"showgrid": False, "title": "Financial Year"},
        yaxis={
            "showgrid": True,
            "gridcolor": "rgba(255, 255, 255, 0.1)",
            "title": "Net Profit (INR Cr)",
        },
    )

    st.plotly_chart(fig, use_container_width=True)


def render_roe_roce_trend(df_ratios: pd.DataFrame):
    """
    Plots a trend line chart for ROE & ROCE across available years.

    Args:
        df_ratios (pd.DataFrame): DataFrame containing financial ratios.
    """
    if df_ratios.empty:
        st.warning("No ratio data available.")
        return

    if "year_int" in df_ratios.columns:
        df_sorted = df_ratios.sort_values("year_int")
    else:
        df_sorted = df_ratios.sort_values("year")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df_sorted["year"],
            y=df_sorted["return_on_equity_pct"],
            name="ROE (%)",
            mode="lines+markers",
            line={"color": "#a29bfe", "width": 3},
            hovertemplate="Year: %{x}<br>ROE: %{y:.2f}%<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df_sorted["year"],
            y=df_sorted["return_on_capital_employed_pct"],
            name="ROCE (%)",
            mode="lines+markers",
            line={"color": "#00b894", "width": 3},
            hovertemplate="Year: %{x}<br>ROCE: %{y:.2f}%<extra></extra>",
        )
    )

    fig.update_layout(
        margin={"t": 30, "b": 10, "l": 10, "r": 10},
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#ffffff"},
        xaxis={"showgrid": False, "title": "Financial Year"},
        yaxis={
            "showgrid": True, "gridcolor": "rgba(255, 255, 255, 0.1)", "title": "Percentage (%)"
        },
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    st.plotly_chart(fig, use_container_width=True)
