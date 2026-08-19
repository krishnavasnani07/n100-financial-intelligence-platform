import pytest

from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import calculate_cfo_quality
from src.analytics.ratios import (
    calculate_debt_to_equity,
    calculate_high_leverage_flag,
    calculate_icr_warning,
    calculate_interest_coverage,
    calculate_operating_profit_margin,
    calculate_roe,
)


# 1. ROE with positive equity
def test_roe_positive_equity():
    # Net Income = 100, Equity Capital = 100, Reserves = 400 => total equity = 500
    # Expected ROE = 100 / 500 = 20%
    result = calculate_roe(100, 100, 400)
    assert result == pytest.approx(20.0)


# 2. ROE with negative equity
def test_roe_negative_equity():
    # Net Income = 100, Equity Capital = -500, Reserves = 0 => total equity = -500
    # Expected ROE = None
    result = calculate_roe(100, -500, 0)
    assert result is None


# 3. Debt-free company D/E
def test_de_debt_free():
    # Borrowings = 0, Equity Capital = 100, Reserves = 400 => D/E = 0.0
    result = calculate_debt_to_equity(0, 100, 400)
    assert result == 0.0


# 4. High D/E flag (triggers flag)
def test_de_high_leverage():
    # D/E = 5.5, is_financial = False, threshold = 5.0 => triggers flag
    result = calculate_high_leverage_flag(5.5, is_financial=False, threshold=5.0)
    assert result is True


# 5. Moderate D/E flag (does not trigger flag)
def test_de_no_high_leverage():
    # D/E = 4.5, is_financial = False, threshold = 5.0 => does not trigger
    result = calculate_high_leverage_flag(4.5, is_financial=False, threshold=5.0)
    assert result is False


# 6. D/E flag ignored for financial companies
def test_de_financial_ignored():
    # D/E = 10.0, is_financial = True, threshold = 5.0 => does not trigger
    result = calculate_high_leverage_flag(10.0, is_financial=True, threshold=5.0)
    assert result is False


# 7. ICR when interest = 0 (skipped / returns None)
def test_icr_zero_interest():
    # Operating Profit = 100, Interest = 0
    result = calculate_interest_coverage(100, 0)
    assert result is None


# 8. ICR normal case
def test_icr_normal_case():
    # Operating Profit = 80, Interest = 20, Other Income = 20 => EBIT = 100
    # Expected ICR = 100 / 20 = 5.0
    result = calculate_interest_coverage(80, 20, other_income=20)
    assert result == pytest.approx(5.0)


# 9. ICR warning triggered
def test_icr_warning_triggered():
    # ICR = 1.2, threshold = 1.5 => triggers warning (True)
    result = calculate_icr_warning(1.2, threshold=1.5)
    assert result is True


# 10. ICR warning not triggered
def test_icr_warning_not_triggered():
    # ICR = 3.0, threshold = 1.5 => does not trigger warning (False)
    result = calculate_icr_warning(3.0, threshold=1.5)
    assert result is False


# 11. Normal CAGR
def test_cagr_normal():
    # Start = 100, End = 121, Years = 2 => (121/100)^(1/2) - 1 = 10%
    val, flag = calculate_cagr(100, 121, 2)
    assert val == pytest.approx(10.0)
    assert flag == "VALID"


# 12. CAGR turnaround (Negative to Positive)
def test_cagr_turnaround():
    # Start = -100, End = 100 => returns None, status TURNAROUND
    val, flag = calculate_cagr(-100, 100, 2)
    assert val is None
    assert flag == "TURNAROUND"


# 13. CAGR decline-to-loss (Positive to Negative/Zero)
def test_cagr_decline_to_loss():
    # Start = 100, End = -50 => returns None, status DECLINE_TO_LOSS
    val, flag = calculate_cagr(100, -50, 2)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"


# 14. CAGR both negative
def test_cagr_both_negative():
    # Start = -100, End = -50 => returns None, status BOTH_NEGATIVE
    val, flag = calculate_cagr(-100, -50, 2)
    assert val is None
    assert flag == "BOTH_NEGATIVE"


# 15. CAGR zero base
def test_cagr_zero_base():
    # Start = 0, End = 100 => returns None, status ZERO_BASE
    val, flag = calculate_cagr(0, 100, 2)
    assert val is None
    assert flag == "ZERO_BASE"


# 16. CAGR insufficient periods
def test_cagr_insufficient_periods():
    # Years = 0
    val, flag = calculate_cagr(100, 121, 0)
    assert val is None
    assert flag == "INSUFFICIENT"


# 17. OPM cross check no divergence
def test_opm_cross_check_no_divergence():
    # Operating Profit = 10, Sales = 100, Reported OPM = 10.0 => matches
    result = calculate_operating_profit_margin(
        10, 100, reported_opm=10.0, tolerance=1.0
    )
    assert result == pytest.approx(10.0)


# 18. OPM cross check divergence
def test_opm_cross_check_divergence():
    # Operating Profit = 10, Sales = 100, Reported OPM = 15.0 => computed is 10.0, diff = 5.0 > tolerance (1.0)
    result = calculate_operating_profit_margin(
        10, 100, reported_opm=15.0, tolerance=1.0
    )
    assert result == pytest.approx(10.0)


# 19. CFO quality score normal positive case
def test_cfo_quality_positive():
    # Operating Cash Flow = 120, PAT = 100 => ratio = 1.2
    result = calculate_cfo_quality(120, 100)
    assert result == pytest.approx(1.2)


# 20. CFO quality score negative/zero PAT
def test_cfo_quality_negative_pat():
    # PAT <= 0 => returns None
    result = calculate_cfo_quality(120, -50)
    assert result is None
