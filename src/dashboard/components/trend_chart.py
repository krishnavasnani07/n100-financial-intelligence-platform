import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render_trend_charts(df: pd.DataFrame, selected_metrics: list, metric_map: dict):
    """
    Renders 10-year trend charts for selected metrics.
    Plots each metric in its own container to handle different scaling properly.
    """
    if df.empty or not selected_metrics:
        st.info("Please select at least one metric to display the trends.")
        return

    # Sort chronologically by year_int
    df_sorted = df.sort_values("year_int").copy()

    # Custom color palette for charts
    colors = ["#a29bfe", "#00b894", "#fdcb6e"]

    for idx, metric_name in enumerate(selected_metrics):
        col = metric_map[metric_name]
        color = colors[idx % len(colors)]

        # Calculate YoY percentage change
        df_sorted[f"{col}_yoy"] = df_sorted[col].pct_change() * 100

        # Generate custom hover strings for YoY labels
        hover_texts = []
        for _, row in df_sorted.iterrows():
            val = row[col]
            yoy = row[f"{col}_yoy"]
            if pd.isnull(val):
                hover_texts.append("N/A")
            elif pd.isnull(yoy):
                hover_texts.append(f"Value: {val:,.2f} (YoY: N/A)")
            else:
                sign = "+" if yoy >= 0 else ""
                hover_texts.append(f"Value: {val:,.2f} (YoY: {sign}{yoy:.1f}%)")

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df_sorted["year"],
                y=df_sorted[col],
                name=metric_name,
                mode="lines+markers",
                line=dict(color=color, width=3),
                marker=dict(size=8, symbol="circle"),
                text=hover_texts,
                hovertemplate="<b>%{x}</b><br>%{text}<extra></extra>",
            )
        )

        # Layout customization
        fig.update_layout(
            title=dict(
                text=f"10-Year Trend: {metric_name}",
                font=dict(size=14, color="#ffffff", family="Inter"),
            ),
            margin=dict(t=40, b=10, l=10, r=10),
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#ffffff"),
            xaxis=dict(showgrid=False, title="", tickangle=0),
            yaxis=dict(showgrid=True, gridcolor="rgba(255, 255, 255, 0.1)", title=""),
            showlegend=False,
        )

        st.plotly_chart(fig, use_container_width=True)
