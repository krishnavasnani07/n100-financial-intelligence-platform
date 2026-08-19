"""
Growth Analytics Engine Configuration.
Defines supported CAGR time windows, metric keys, edge-case flag constants,
growth classification thresholds, and output formatting precision.
"""


# Supported CAGR calculation time windows (in years)
CAGR_TIME_WINDOWS: list[int] = [3, 5, 10]

# Supported growth metrics mapping (Database column -> Display Name)
CAGR_METRICS: dict[str, str] = {"sales": "Revenue", "net_profit": "PAT", "eps": "EPS"}

# CAGR Edge Case Flag Constants
FLAG_VALID: str = "VALID"
FLAG_DECLINE_TO_LOSS: str = "DECLINE_TO_LOSS"
FLAG_TURNAROUND: str = "TURNAROUND"
FLAG_BOTH_NEGATIVE: str = "BOTH_NEGATIVE"
FLAG_ZERO_BASE: str = "ZERO_BASE"
FLAG_INSUFFICIENT: str = "INSUFFICIENT"
FLAG_INVALID_INPUT: str = "INVALID_INPUT"

# Growth Classification Labels & Thresholds (CAGR %)
GROWTH_CLASSIFICATION_THRESHOLDS: dict[str, float] = {
    "HIGH_GROWTH": 20.0,  # > 20%
    "STRONG_GROWTH": 10.0,  # 10% - 20%
    "MODERATE_GROWTH": 5.0,  # 5% - 10%
    "SLOW_GROWTH": 0.0,  # 0% - 5%
}

# Growth Classification Display Names
LABEL_HIGH_GROWTH: str = "High Growth"
LABEL_STRONG_GROWTH: str = "Strong Growth"
LABEL_MODERATE_GROWTH: str = "Moderate"
LABEL_SLOW_GROWTH: str = "Slow"
LABEL_DECLINING: str = "Declining"
LABEL_NOT_APPLICABLE: str = "N/A"

# Calculation Precision
DEFAULT_CAGR_PRECISION: int = 2
