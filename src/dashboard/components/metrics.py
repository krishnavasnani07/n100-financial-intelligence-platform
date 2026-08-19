from src.dashboard.components.cards import kpi_card
from src.dashboard.utils.formatting import (
    format_currency_cr,
    format_percentage,
    format_ratio,
)


def render_financial_metric(
    name: str,
    value: float,
    format_type: str,
    delta: str | None = None,
    delta_type: str = "neutral",
):
    """
    Formates and renders a financial metric inside a glassmorphism KPI card.

    Args:
        name (str): Display name of the metric
        value (float): Numerical value of the metric
        format_type (str): 'percentage', 'currency', or 'ratio'
        delta (str, optional): Additional text/comparison info
        delta_type (str, optional): Color coding for the delta indicator
    """
    if format_type == "percentage":
        formatted_val = format_percentage(value)
    elif format_type == "currency":
        formatted_val = format_currency_cr(value)
    elif format_type == "ratio":
        formatted_val = format_ratio(value)
    else:
        formatted_val = str(value) if value is not None else "N/A"

    kpi_card(name, formatted_val, delta, delta_type)
