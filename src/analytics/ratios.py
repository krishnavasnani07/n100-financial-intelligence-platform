"""
Profitability Ratio Engine for Nifty 100 Financial Intelligence Platform.
Calculates key profitability metrics: NPM, OPM, ROE, ROCE, and ROA.
Includes safe division helpers, cross-check anomaly logging, and financial company handling.
"""

import math
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from src.utils.logger import get_logger
from src.config.settings import BASE_DIR

# Establish dedicated ratio logger writing to logs/ratio_engine.log
def _setup_ratio_logger() -> logging.Logger:
    logger = logging.getLogger("ratio_engine")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        log_dir = BASE_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "ratio_engine.log"
        
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Also add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

ratio_logger = _setup_ratio_logger()


def safe_divide(
    numerator: Any,
    denominator: Any,
    multiplier: float = 1.0,
    precision: int = 2
) -> Optional[float]:
    """
    Safely divide two numbers and apply a multiplier (default 1.0 or 100 for percentages).
    Returns None if numerator/denominator are None, NaN, zero (denominator), or invalid.

    Args:
        numerator: Dividend numeric value.
        denominator: Divisor numeric value.
        multiplier: Scaling multiplier (e.g., 100.0 for percentages).
        precision: Decimal rounding precision.

    Returns:
        Optional[float]: Computed result rounded to precision, or None.
    """
    if numerator is None or denominator is None:
        return None

    try:
        num = float(numerator)
        den = float(denominator)

        if math.isnan(num) or math.isnan(den) or math.isinf(num) or math.isinf(den):
            return None

        if den == 0.0:
            return None

        result = (num / den) * multiplier
        return round(result, precision)

    except (ValueError, TypeError, OverflowError):
        return None


def calculate_net_profit_margin(
    net_profit: Any,
    sales: Any,
    precision: int = 2
) -> Optional[float]:
    """
    Calculate Net Profit Margin (NPM): (Net Profit / Sales) * 100
    Returns None if Sales <= 0 or invalid.
    """
    try:
        sales_val = float(sales)
        if sales_val <= 0:
            return None
    except (ValueError, TypeError):
        return None

    return safe_divide(net_profit, sales, multiplier=100.0, precision=precision)


def calculate_operating_profit_margin(
    operating_profit: Any,
    sales: Any,
    reported_opm: Optional[Any] = None,
    company_id: str = "UNKNOWN",
    year: str = "UNKNOWN",
    tolerance: float = 1.0,
    precision: int = 2
) -> Optional[float]:
    """
    Calculate Operating Profit Margin (OPM): (Operating Profit / Sales) * 100
    Cross-checks calculated OPM against reported_opm if provided and logs anomalies.

    Args:
        operating_profit: Operating profit amount.
        sales: Sales/Revenue amount.
        reported_opm: OPM percentage reported in raw source file.
        company_id: Ticker for logging.
        year: Year for logging.
        tolerance: Threshold difference percentage for anomaly logging (default 1.0%).
        precision: Rounding decimal places.

    Returns:
        Optional[float]: Calculated OPM percentage or None.
    """
    try:
        sales_val = float(sales)
        if sales_val <= 0:
            return None
    except (ValueError, TypeError):
        return None

    computed_opm = safe_divide(operating_profit, sales, multiplier=100.0, precision=precision)

    if computed_opm is not None and reported_opm is not None:
        try:
            rep_opm_val = float(reported_opm)
            if not math.isnan(rep_opm_val):
                diff = abs(computed_opm - rep_opm_val)
                if diff > tolerance:
                    ratio_logger.warning(
                        f"OPM mismatch for {company_id} ({year}): Expected {rep_opm_val:.2f}%, "
                        f"Computed {computed_opm:.2f}% (diff={diff:.2f}%)"
                    )
                else:
                    ratio_logger.info(
                        f"OPM cross-check matched for {company_id} ({year}): {computed_opm:.2f}%"
                    )
        except (ValueError, TypeError):
            pass

    return computed_opm


def calculate_roe(
    net_profit: Any,
    equity_capital: Any,
    reserves: Any,
    precision: int = 2
) -> Optional[float]:
    """
    Calculate Return on Equity (ROE): (Net Profit / (Equity Capital + Reserves)) * 100
    Returns None if total equity (Equity Capital + Reserves) <= 0 or invalid.
    """
    try:
        eq = float(equity_capital) if equity_capital is not None else 0.0
        res = float(reserves) if reserves is not None else 0.0
        total_equity = eq + res
        if total_equity <= 0:
            return None
    except (ValueError, TypeError):
        return None

    return safe_divide(net_profit, total_equity, multiplier=100.0, precision=precision)


def calculate_roce(
    ebit_or_op: Any,
    equity_capital: Any,
    reserves: Any,
    borrowings: Any,
    is_financial: bool = False,
    company_id: str = "UNKNOWN",
    year: str = "UNKNOWN",
    precision: int = 2
) -> Optional[float]:
    """
    Calculate Return on Capital Employed (ROCE):
    EBIT / (Equity Capital + Reserves + Borrowings) * 100

    Args:
        ebit_or_op: Operating Profit or EBIT.
        equity_capital: Equity Capital value.
        reserves: Reserves & Surplus value.
        borrowings: Total Borrowings/Debt value.
        is_financial: Flag indicating if the company is in Financials sector.
        company_id: Ticker for logging.
        year: Year for logging.
        precision: Rounding decimal places.

    Returns:
        Optional[float]: Calculated ROCE percentage or None.
    """
    try:
        eq = float(equity_capital) if equity_capital is not None else 0.0
        res = float(reserves) if reserves is not None else 0.0
        borr = float(borrowings) if borrowings is not None else 0.0
        capital_employed = eq + res + borr

        if capital_employed <= 0:
            return None
    except (ValueError, TypeError):
        return None

    if is_financial:
        ratio_logger.info(
            f"ROCE calculated for financial sector entity {company_id} ({year}) - "
            f"Requires sector-relative evaluation."
        )

    return safe_divide(ebit_or_op, capital_employed, multiplier=100.0, precision=precision)


def calculate_roa(
    net_profit: Any,
    total_assets: Any,
    precision: int = 2
) -> Optional[float]:
    """
    Calculate Return on Assets (ROA): (Net Profit / Total Assets) * 100
    Returns None if Total Assets <= 0 or invalid.
    """
    try:
        assets_val = float(total_assets)
        if assets_val <= 0:
            return None
    except (ValueError, TypeError):
        return None

    return safe_divide(net_profit, total_assets, multiplier=100.0, precision=precision)


class ProfitabilityEngine:
    """
    High-level engine to calculate all 5 profitability ratios for financial records.
    """

    @staticmethod
    def compute_all_ratios(
        company_id: str,
        year: str,
        sales: Any,
        operating_profit: Any,
        net_profit: Any,
        equity_capital: Any,
        reserves: Any,
        borrowings: Any,
        total_assets: Any,
        reported_opm: Optional[Any] = None,
        is_financial: bool = False
    ) -> Dict[str, Optional[float]]:
        """
        Compute all 5 profitability ratios for a single period.

        Returns:
            Dict containing npm, opm, roe, roce, roa.
        """
        npm = calculate_net_profit_margin(net_profit, sales)
        opm = calculate_operating_profit_margin(
            operating_profit, sales, reported_opm=reported_opm, company_id=company_id, year=year
        )
        roe = calculate_roe(net_profit, equity_capital, reserves)
        roce = calculate_roce(
            operating_profit, equity_capital, reserves, borrowings, is_financial=is_financial, company_id=company_id, year=year
        )
        roa = calculate_roa(net_profit, total_assets)

        ratio_logger.info(
            f"Calculated Ratios for {company_id} ({year}) -> "
            f"NPM: {npm}%, OPM: {opm}%, ROE: {roe}%, ROCE: {roce}%, ROA: {roa}%"
        )

        return {
            "company_id": company_id,
            "year": year,
            "npm": npm,
            "opm": opm,
            "roe": roe,
            "roce": roce,
            "roa": roa,
        }
