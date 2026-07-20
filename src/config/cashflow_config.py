"""
Cash Flow Analytics Engine Configuration (Sprint 2 - Day 11).
Defines thresholds for CFO Quality, CapEx Intensity, and Pattern Mappings for Capital Allocation.
"""

from typing import Dict, Tuple

# Numerical Precision
DEFAULT_CASHFLOW_PRECISION: int = 2

# CFO Quality Thresholds (Operating Cash Flow / Net Profit)
CFO_QUALITY_HIGH_THRESHOLD: float = 1.0
CFO_QUALITY_MODERATE_THRESHOLD: float = 0.5

# CFO Quality Display Labels
LABEL_CFO_HIGH: str = "High"
LABEL_CFO_MODERATE: str = "Moderate"
LABEL_CFO_ACCRUAL_RISK: str = "Accrual Risk"

# CapEx Intensity Thresholds (ABS(CFI) / Sales * 100)
CAPEX_ASSET_LIGHT_THRESHOLD: float = 3.0
CAPEX_INTENSIVE_THRESHOLD: float = 8.0

# CapEx Intensity Display Labels
LABEL_CAPEX_ASSET_LIGHT: str = "Asset Light"
LABEL_CAPEX_MODERATE: str = "Moderate"
LABEL_CAPEX_INTENSIVE: str = "Capital Intensive"

# Capital Allocation Pattern Map: (cfo_sign, cfi_sign, cff_sign) -> pattern_label
PATTERN_MAP: Dict[Tuple[str, str, str], str] = {
    ("+", "-", "-"): "Reinvestor",
    ("+", "+", "-"): "Liquidating Assets",
    ("-", "+", "+"): "Distress Signal",
    ("-", "-", "+"): "Growth Funded by Debt",
    ("+", "+", "+"): "Cash Accumulator",
    ("-", "-", "-"): "Pre-Revenue",
    ("+", "-", "+"): "Mixed",
    ("-", "+", "-"): "Distress Signal",
}

LABEL_SHAREHOLDER_RETURNS: str = "Shareholder Returns"
