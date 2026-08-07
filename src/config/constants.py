"""
Centralized configuration constants, scoring weights, and preset filters for the Nifty 100 Financial Intelligence Platform.
"""

# Winsorization Quantiles
WINSOR_LOWER_QUANTILE = 0.10
WINSOR_UPPER_QUANTILE = 0.90

# Composite Quality Score Weights
QUALITY_SCORE_WEIGHTS = {
    "roe_score": 0.15,
    "roce_score": 0.10,
    "npm_score": 0.10,
    "fcf_cagr_score": 0.15,
    "cfo_pat_score": 0.10,
    "fcf_flag_score": 0.05,
    "rev_cagr_score": 0.10,
    "pat_cagr_score": 0.10,
    "de_score": 0.10,
    "icr_score": 0.05,
}

# Predefined Screener Preset Criteria
QUALITY_COMPOUNDER_CRITERIA = {
    "filters": {
        "min_roe": 15.0,
        "max_debt_to_equity": 1.0,
        "min_fcf": 0.0,
        "min_revenue_cagr_5yr": 10.0,
    }
}

VALUE_PICK_CRITERIA = {
    "filters": {
        "max_pe": 20.0,
        "max_pb": 3.0,
        "max_debt_to_equity": 2.0,
        "min_dividend_yield": 1.0,
    }
}

GROWTH_ACCELERATOR_CRITERIA = {
    "filters": {
        "min_pat_cagr_5yr": 20.0,
        "min_revenue_cagr_5yr": 15.0,
        "max_debt_to_equity": 2.0,
    }
}

DIVIDEND_CHAMPION_CRITERIA = {
    "filters": {
        "min_dividend_yield": 2.0,
        "max_dividend_payout": 80.0,
        "min_fcf": 0.0,
    }
}

DEBT_FREE_BLUE_CHIP_CRITERIA = {
    "filters": {
        "max_debt_to_equity": 0.0,
        "min_roe": 12.0,
        "min_sales": 5000.0,
    }
}

TURNAROUND_WATCH_CRITERIA = {
    "filters": {
        "min_fcf": 0.0,
        "min_revenue_cagr_3yr": 10.0,
    }
}
