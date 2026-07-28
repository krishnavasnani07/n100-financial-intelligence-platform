def format_currency_cr(value: float) -> str:
    """Formats values in Crores (INR)"""
    if value is None or not isinstance(value, (int, float)):
        return "N/A"
    return f"₹{value:,.2f} Cr"

def format_percentage(value: float) -> str:
    """Formats percentage values"""
    if value is None or not isinstance(value, (int, float)):
        return "N/A"
    return f"{value:.2f}%"

def format_ratio(value: float) -> str:
    """Formats ratios like P/E, D/E, Asset Turnover"""
    if value is None or not isinstance(value, (int, float)):
        return "N/A"
    return f"{value:.2f}x"
