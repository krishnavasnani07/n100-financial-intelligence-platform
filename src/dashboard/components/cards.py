import streamlit as st

def kpi_card(title: str, value: str, delta: str = None, delta_type: str = "neutral"):
    """
    Renders a premium glassmorphic metric/KPI card using custom HTML/CSS.
    
    Args:
        title (str): Title of the metric
        value (str): Value of the metric
        delta (str, optional): Change or detail string shown below value
        delta_type (str, optional): 'positive' (green), 'negative' (red), or 'neutral' (yellow)
    """
    delta_html = ""
    if delta:
        delta_html = f'<div class="kpi-delta {delta_type}">{delta}</div>'
        
    card_html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
