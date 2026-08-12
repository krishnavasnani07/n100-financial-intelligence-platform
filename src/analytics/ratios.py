"""
Profitability Ratio Engine for Nifty 100 Financial Intelligence Platform (Enhanced).
Calculates NPM, OPM, ROE, ROCE, and ROA utilizing RatioCalculator base, ratio_config, and structured RatioResult models.
Outputs detailed calculation logs (output/ratio_calculation_log.csv), ratio summaries, and performance metrics.
"""

import csv
import logging
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.analytics.ratio_base import RatioCalculator, RatioResult
from src.config.ratio_config import (
    ASSET_TURNOVER_BENCHMARKS,
    DEBT_TO_EQUITY_BENCHMARKS,
    DEFAULT_PRECISION,
    HIGH_LEVERAGE_THRESHOLD,
    ICR_BENCHMARKS,
    ICR_WARNING_THRESHOLD,
    NPM_BENCHMARKS,
    OPM_BENCHMARKS,
    OPM_TOLERANCE,
    ROA_BENCHMARKS,
    ROCE_BENCHMARKS,
    ROE_BENCHMARKS,
)
from src.config.settings import BASE_DIR
from src.utils.logger import get_logger

# Setup dedicated ratio logger
ratio_logger = get_logger("ratio_engine")


def safe_divide(
    numerator: Any,
    denominator: Any,
    multiplier: float = 1.0,
    precision: int = DEFAULT_PRECISION,
) -> Optional[float]:
    """
    Safely divides numerator by denominator, handling exceptions and rounding.

    Parameters:
        numerator (Any): Numerator value.
        denominator (Any): Denominator value.
        multiplier (float): Scaling multiplier.
        precision (int): Rounding decimal precision.

    Returns:
        Optional[float]: Computed result or None if division fails.
    """
    val, _ = RatioCalculator.safe_divide(
        numerator, denominator, multiplier=multiplier, precision=precision
    )
    return val


def calculate_net_profit_margin(
    net_profit: Any, sales: Any, precision: int = DEFAULT_PRECISION
) -> Optional[float]:
    """
    Computes Net Profit Margin percentage.

    Parameters:
        net_profit (Any): Net profit value.
        sales (Any): Net sales value.
        precision (int): Rounding decimal precision.

    Returns:
        Optional[float]: NPM value or None.
    """
    try:
        if float(sales) <= 0:
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
    tolerance: float = OPM_TOLERANCE,
    precision: int = DEFAULT_PRECISION,
) -> Optional[float]:
    """
    Computes Operating Profit Margin and validates against reported OPM.

    Parameters:
        operating_profit (Any): Operating profit value.
        sales (Any): Net sales value.
        reported_opm (Optional[Any]): Reported OPM from company financials.
        company_id (str): ID of the company.
        year (str): Financial year.
        tolerance (float): Maximum discrepancy allowed before logging mismatch.
        precision (int): Rounding decimal precision.

    Returns:
        Optional[float]: Computed OPM value or None.
    """
    try:
        if float(sales) <= 0:
            return None
    except (ValueError, TypeError):
        return None

    computed_opm = safe_divide(
        operating_profit, sales, multiplier=100.0, precision=precision
    )

    if computed_opm is not None and reported_opm is not None:
        try:
            rep_opm_val = float(reported_opm)
            if not math.isnan(rep_opm_val):
                diff = abs(computed_opm - rep_opm_val)
                if diff > tolerance:
                    ratio_logger.warning(
                        f"OPM mismatch for {company_id} ({year}): Expected {rep_opm_val:.2f}%, Computed {computed_opm:.2f}% (diff={diff:.2f}%)"
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
    precision: int = DEFAULT_PRECISION,
) -> Optional[float]:
    """
    Computes Return on Equity percentage.

    Parameters:
        net_profit (Any): Net profit value.
        equity_capital (Any): Equity capital value.
        reserves (Any): Reserves value.
        precision (int): Rounding decimal precision.

    Returns:
        Optional[float]: ROE value or None.
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
    precision: int = DEFAULT_PRECISION,
) -> Optional[float]:
    """
    Computes Return on Capital Employed percentage.

    Parameters:
        ebit_or_op (Any): EBIT or Operating profit.
        equity_capital (Any): Equity capital value.
        reserves (Any): Reserves value.
        borrowings (Any): Borrowings value.
        is_financial (bool): True if the company is in the Financial sector.
        company_id (str): ID of the company.
        year (str): Financial year.
        precision (int): Rounding decimal precision.

    Returns:
        Optional[float]: ROCE value or None.
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
            f"ROCE calculated for financial sector entity {company_id} ({year}) - Requires sector-relative evaluation."
        )

    return safe_divide(
        ebit_or_op, capital_employed, multiplier=100.0, precision=precision
    )


def calculate_roa(
    net_profit: Any, total_assets: Any, precision: int = DEFAULT_PRECISION
) -> Optional[float]:
    """
    Computes Return on Assets percentage.

    Parameters:
        net_profit (Any): Net profit value.
        total_assets (Any): Total assets value.
        precision (int): Rounding decimal precision.

    Returns:
        Optional[float]: ROA value or None.
    """
    try:
        if float(total_assets) <= 0:
            return None
    except (ValueError, TypeError):
        return None

    return safe_divide(net_profit, total_assets, multiplier=100.0, precision=precision)


def calculate_debt_to_equity(
    borrowings: Any,
    equity_capital: Any,
    reserves: Any,
    company_id: str = "UNKNOWN",
    year: str = "UNKNOWN",
    precision: int = DEFAULT_PRECISION,
) -> Optional[float]:
    """
    Computes Debt-to-Equity ratio.

    Parameters:
        borrowings (Any): Borrowings value.
        equity_capital (Any): Equity capital value.
        reserves (Any): Reserves value.
        company_id (str): ID of the company.
        year (str): Financial year.
        precision (int): Rounding decimal precision.

    Returns:
        Optional[float]: D/E ratio value or None.
    """
    try:
        eq = float(equity_capital) if equity_capital is not None else 0.0
        res = float(reserves) if reserves is not None else 0.0
        tot_eq = eq + res
        if tot_eq <= 0:
            return None

        borr = float(borrowings) if borrowings is not None else 0.0
        if borr == 0:
            ratio_logger.info(f"Calculated Debt-to-Equity {company_id} {year} 0.0")
            return 0.0

        de_val = safe_divide(borr, tot_eq, multiplier=1.0, precision=precision)
        if de_val is not None:
            ratio_logger.info(
                f"Calculated Debt-to-Equity {company_id} {year} {de_val:.2f}"
            )
        return de_val
    except (ValueError, TypeError):
        return None


def calculate_high_leverage_flag(
    de_ratio: Optional[float],
    is_financial: bool = False,
    threshold: float = HIGH_LEVERAGE_THRESHOLD,
    company_id: str = "UNKNOWN",
) -> bool:
    """
    Checks if Debt-to-Equity ratio indicates high leverage.

    Parameters:
        de_ratio (Optional[float]): Debt-to-Equity ratio.
        is_financial (bool): True if financial sector company.
        threshold (float): High leverage threshold value.
        company_id (str): ID of the company.

    Returns:
        bool: True if highly leveraged, False otherwise.
    """
    if de_ratio is None or is_financial:
        return False
    if de_ratio > threshold:
        ratio_logger.warning(f"High Leverage {company_id} D/E = {de_ratio:.1f}")
        return True
    return False


def calculate_interest_coverage(
    operating_profit: Any,
    interest: Any,
    other_income: Any = 0,
    precision: int = DEFAULT_PRECISION,
) -> Optional[float]:
    """
    Computes Interest Coverage Ratio.

    Parameters:
        operating_profit (Any): Operating profit value.
        interest (Any): Interest value.
        other_income (Any): Other income value.
        precision (int): Rounding decimal precision.

    Returns:
        Optional[float]: Interest Coverage Ratio value or None.
    """
    try:
        intr = float(interest) if interest is not None else None
        if intr is None or intr == 0:
            ratio_logger.info("Debt Free Company ICR skipped")
            return None
        if intr < 0:
            return None

        op = float(operating_profit) if operating_profit is not None else 0.0
        oth = float(other_income) if other_income is not None else 0.0
        tot_inc = op + oth
        return safe_divide(tot_inc, intr, multiplier=1.0, precision=precision)
    except (ValueError, TypeError):
        return None


def calculate_icr_warning(
    icr_ratio: Optional[float], threshold: float = ICR_WARNING_THRESHOLD
) -> bool:
    """
    Checks if Interest Coverage Ratio triggers warning threshold.

    Parameters:
        icr_ratio (Optional[float]): Interest Coverage Ratio.
        threshold (float): Warning threshold value.

    Returns:
        bool: True if ICR is below threshold, False otherwise.
    """
    if icr_ratio is None:
        return False
    return icr_ratio < threshold


def calculate_icr_label(
    interest: Any, icr_ratio: Optional[float] = None
) -> Optional[str]:
    """
    Determines qualitative status label for Interest Coverage Ratio.

    Parameters:
        interest (Any): Interest value.
        icr_ratio (Optional[float]): Interest Coverage Ratio value.

    Returns:
        Optional[str]: Quality label ("Debt Free", "Strong", "Healthy", "Watch", "Risky").
    """
    try:
        if interest is not None and float(interest) == 0:
            return "Debt Free"
    except (ValueError, TypeError):
        pass

    if icr_ratio is not None:
        if icr_ratio >= 5.0:
            return "Strong"
        elif icr_ratio >= 2.0:
            return "Healthy"
        elif icr_ratio >= 1.5:
            return "Watch"
        else:
            return "Risky"
    return None


def calculate_net_debt(
    borrowings: Any, investments: Any, precision: int = DEFAULT_PRECISION
) -> Optional[float]:
    """
    Computes Net Debt.

    Parameters:
        borrowings (Any): Borrowings value.
        investments (Any): Investments value.
        precision (int): Rounding decimal precision.

    Returns:
        Optional[float]: Net Debt value or None.
    """
    try:
        borr = float(borrowings) if borrowings is not None else 0.0
        inv = float(investments) if investments is not None else 0.0
        return round(borr - inv, precision)
    except (ValueError, TypeError):
        return None


def calculate_asset_turnover(
    sales: Any, total_assets: Any, precision: int = DEFAULT_PRECISION
) -> Optional[float]:
    """
    Computes Asset Turnover Ratio.

    Parameters:
        sales (Any): Net sales value.
        total_assets (Any): Total assets value.
        precision (int): Rounding decimal precision.

    Returns:
        Optional[float]: Asset Turnover value or None.
    """
    try:
        ta = float(total_assets) if total_assets is not None else 0.0
        if ta <= 0:
            return None
        s = float(sales) if sales is not None else 0.0
        return safe_divide(s, ta, multiplier=1.0, precision=precision)
    except (ValueError, TypeError):
        return None


class ProfitabilityEngine(RatioCalculator):
    """
    Enhanced Profitability Analytics Engine.
    Computes KPIs, returns RatioResult objects, logs to CSV, and generates ratio summary statistics.
    """

    @classmethod
    def compute_period_ratios(
        cls,
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
        is_financial: bool = False,
    ) -> List[RatioResult]:
        results: List[RatioResult] = []

        # 1. NPM
        val_npm, status_npm = cls.safe_divide(net_profit, sales, multiplier=100.0)
        if sales is not None and float(sales or 0) <= 0:
            status_npm = "NON_POSITIVE_SALES"
            val_npm = None
        results.append(
            cls.create_result(
                company_id,
                year,
                "NPM",
                val_npm,
                status_npm,
                "Net Profit / Sales * 100",
                "profitandloss",
                NPM_BENCHMARKS,
            )
        )

        # 2. OPM
        val_opm, status_opm = cls.safe_divide(operating_profit, sales, multiplier=100.0)
        if sales is not None and float(sales or 0) <= 0:
            status_opm = "NON_POSITIVE_SALES"
            val_opm = None
        if val_opm is not None and reported_opm is not None:
            try:
                diff = abs(val_opm - float(reported_opm))
                if diff > OPM_TOLERANCE:
                    status_opm = "OPM_MISMATCH"
                    ratio_logger.warning(
                        f"OPM mismatch for {company_id} ({year}): Expected {reported_opm}%, Computed {val_opm:.2f}%"
                    )
            except (ValueError, TypeError):
                pass
        results.append(
            cls.create_result(
                company_id,
                year,
                "OPM",
                val_opm,
                status_opm,
                "Operating Profit / Sales * 100",
                "profitandloss",
                OPM_BENCHMARKS,
            )
        )

        # 3. ROE
        eq = float(equity_capital or 0)
        res = float(reserves or 0)
        tot_eq = eq + res
        val_roe, status_roe = cls.safe_divide(net_profit, tot_eq, multiplier=100.0)
        if tot_eq <= 0:
            status_roe = "NON_POSITIVE_EQUITY"
            val_roe = None
        results.append(
            cls.create_result(
                company_id,
                year,
                "ROE",
                val_roe,
                status_roe,
                "PAT / (Equity + Reserves) * 100",
                "profitandloss + balancesheet",
                ROE_BENCHMARKS,
            )
        )

        # 4. ROCE
        borr = float(borrowings or 0)
        cap_emp = tot_eq + borr
        val_roce, status_roce = cls.safe_divide(
            operating_profit, cap_emp, multiplier=100.0
        )
        if cap_emp <= 0:
            status_roce = "NON_POSITIVE_CAPITAL_EMPLOYED"
            val_roce = None
        if is_financial:
            ratio_logger.info(
                f"ROCE calculated for financial entity {company_id} ({year})"
            )
        results.append(
            cls.create_result(
                company_id,
                year,
                "ROCE",
                val_roce,
                status_roce,
                "EBIT / Capital Employed * 100",
                "profitandloss + balancesheet",
                ROCE_BENCHMARKS,
            )
        )

        # 5. ROA
        val_roa, status_roa = cls.safe_divide(
            net_profit, total_assets, multiplier=100.0
        )
        if total_assets is not None and float(total_assets or 0) <= 0:
            status_roa = "NON_POSITIVE_ASSETS"
            val_roa = None
        results.append(
            cls.create_result(
                company_id,
                year,
                "ROA",
                val_roa,
                status_roa,
                "PAT / Total Assets * 100",
                "profitandloss + balancesheet",
                ROA_BENCHMARKS,
            )
        )

        return results

    @classmethod
    def compute_all_ratios(
        cls,
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
        is_financial: bool = False,
    ) -> Dict[str, Optional[float]]:
        """Legacy compatibility wrapper returning dictionary of ratio values."""
        rlist = cls.compute_period_ratios(
            company_id,
            year,
            sales,
            operating_profit,
            net_profit,
            equity_capital,
            reserves,
            borrowings,
            total_assets,
            reported_opm,
            is_financial,
        )
        res_map = {r.ratio_name.lower(): r.value for r in rlist}
        res_map["company_id"] = company_id
        res_map["year"] = year
        return res_map

    @classmethod
    def export_ratio_audit_and_summary(
        cls, results: List[RatioResult], output_dir: Optional[Path] = None
    ):
        """Export calculation audit log CSV and summary statistics CSV."""
        out_dir = output_dir or (BASE_DIR / "output")
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Calculation Audit Log
        log_file = out_dir / "ratio_calculation_log.csv"
        df_log = pd.DataFrame([r.to_dict() for r in results])
        df_log.to_csv(log_file, index=False)
        ratio_logger.info(f"Exported ratio calculation audit log to {log_file}")

        # 2. Ratio Summary Statistics
        summary_file = out_dir / "ratio_summary.csv"
        summary_rows = []
        for ratio_name in ["NPM", "OPM", "ROE", "ROCE", "ROA"]:
            sub = df_log[df_log["ratio_name"] == ratio_name]
            vals = sub["value"].dropna()
            summary_rows.append(
                {
                    "KPI": ratio_name,
                    "Total_Evaluated": len(sub),
                    "Valid_Count": len(vals),
                    "Null_Count": len(sub) - len(vals),
                    "Average": round(vals.mean(), 2) if not vals.empty else None,
                    "Min": round(vals.min(), 2) if not vals.empty else None,
                    "Max": round(vals.max(), 2) if not vals.empty else None,
                }
            )
        df_summary = pd.DataFrame(summary_rows)
        df_summary.to_csv(summary_file, index=False)
        ratio_logger.info(f"Exported ratio summary statistics to {summary_file}")


class LeverageEngine(RatioCalculator):
    """
    Enhanced Leverage & Efficiency Analytics Engine.
    Computes D/E, ICR, Net Debt, Asset Turnover, high leverage flags, and ICR warning flags.
    """

    @classmethod
    def compute_period_ratios(
        cls,
        company_id: str,
        year: str,
        borrowings: Any,
        equity_capital: Any,
        reserves: Any,
        operating_profit: Any,
        interest: Any,
        investments: Any,
        sales: Any,
        total_assets: Any,
        other_income: Any = 0,
        is_financial: bool = False,
    ) -> List[RatioResult]:
        results: List[RatioResult] = []

        # 1. Debt-to-Equity
        de_val = calculate_debt_to_equity(
            borrowings, equity_capital, reserves, company_id=company_id, year=year
        )
        eq = float(equity_capital or 0)
        res = float(reserves or 0)
        tot_eq = eq + res
        status_de = "VALID"
        if tot_eq <= 0:
            status_de = "NON_POSITIVE_EQUITY"
        elif de_val == 0.0:
            status_de = "DEBT_FREE"

        results.append(
            cls.create_result(
                company_id,
                year,
                "D/E",
                de_val,
                status_de,
                "Borrowings / (Equity + Reserves)",
                "balancesheet",
                DEBT_TO_EQUITY_BENCHMARKS,
            )
        )

        # 2. Interest Coverage Ratio
        icr_val = calculate_interest_coverage(
            operating_profit, interest, other_income=other_income
        )
        status_icr = "VALID"
        try:
            if interest is not None and float(interest) == 0:
                status_icr = "DEBT_FREE"
            elif interest is not None and float(interest) < 0:
                status_icr = "NEGATIVE_INTEREST"
        except (ValueError, TypeError):
            status_icr = "INVALID_INPUT"

        results.append(
            cls.create_result(
                company_id,
                year,
                "ICR",
                icr_val,
                status_icr,
                "(Operating Profit + Other Income) / Interest",
                "profitandloss",
                ICR_BENCHMARKS,
            )
        )

        # 3. Net Debt
        net_debt_val = calculate_net_debt(borrowings, investments)
        status_nd = "VALID" if net_debt_val is not None else "INVALID_INPUT"
        results.append(
            cls.create_result(
                company_id,
                year,
                "NET_DEBT",
                net_debt_val,
                status_nd,
                "Borrowings - Investments",
                "balancesheet",
                None,
            )
        )

        # 4. Asset Turnover
        at_val = calculate_asset_turnover(sales, total_assets)
        status_at = "VALID"
        if total_assets is not None and float(total_assets or 0) <= 0:
            status_at = "NON_POSITIVE_ASSETS"

        results.append(
            cls.create_result(
                company_id,
                year,
                "ASSET_TURNOVER",
                at_val,
                status_at,
                "Sales / Total Assets",
                "profitandloss + balancesheet",
                ASSET_TURNOVER_BENCHMARKS,
            )
        )

        return results

    @classmethod
    def compute_all_ratios(
        cls,
        company_id: str,
        year: str,
        borrowings: Any,
        equity_capital: Any,
        reserves: Any,
        operating_profit: Any,
        interest: Any,
        investments: Any,
        sales: Any,
        total_assets: Any,
        other_income: Any = 0,
        is_financial: bool = False,
    ) -> Dict[str, Any]:
        rlist = cls.compute_period_ratios(
            company_id,
            year,
            borrowings,
            equity_capital,
            reserves,
            operating_profit,
            interest,
            investments,
            sales,
            total_assets,
            other_income,
            is_financial,
        )
        res_map = {r.ratio_name.lower(): r.value for r in rlist}
        de_val = res_map.get("d/e")
        icr_val = res_map.get("icr")

        res_map["high_leverage_flag"] = calculate_high_leverage_flag(
            de_val, is_financial=is_financial, company_id=company_id
        )
        res_map["icr_warning"] = calculate_icr_warning(icr_val)
        res_map["icr_label"] = calculate_icr_label(interest, icr_val)
        res_map["company_id"] = company_id
        res_map["year"] = year

        return res_map

    @classmethod
    def export_ratio_audit_and_summary(
        cls, results: List[RatioResult], output_dir: Optional[Path] = None
    ):
        """Export calculation audit log CSV and summary statistics CSV for leverage engine."""
        out_dir = output_dir or (BASE_DIR / "output")
        out_dir.mkdir(parents=True, exist_ok=True)

        log_file = out_dir / "leverage_ratio_calculation_log.csv"
        df_log = pd.DataFrame([r.to_dict() for r in results])
        df_log.to_csv(log_file, index=False)
        ratio_logger.info(
            f"Exported leverage ratio calculation audit log to {log_file}"
        )

        summary_file = out_dir / "leverage_ratio_summary.csv"
        summary_rows = []
        for ratio_name in ["D/E", "ICR", "NET_DEBT", "ASSET_TURNOVER"]:
            sub = df_log[df_log["ratio_name"] == ratio_name]
            vals = sub["value"].dropna()
            summary_rows.append(
                {
                    "KPI": ratio_name,
                    "Total_Evaluated": len(sub),
                    "Valid_Count": len(vals),
                    "Null_Count": len(sub) - len(vals),
                    "Average": round(vals.mean(), 2) if not vals.empty else None,
                    "Min": round(vals.min(), 2) if not vals.empty else None,
                    "Max": round(vals.max(), 2) if not vals.empty else None,
                }
            )
        df_summary = pd.DataFrame(summary_rows)
        df_summary.to_csv(summary_file, index=False)
        ratio_logger.info(
            f"Exported leverage ratio summary statistics to {summary_file}"
        )
