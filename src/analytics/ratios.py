"""
Profitability Ratio Engine for Nifty 100 Financial Intelligence Platform (Enhanced).
Calculates NPM, OPM, ROE, ROCE, and ROA utilizing RatioCalculator base, ratio_config, and structured RatioResult models.
Outputs detailed calculation logs (output/ratio_calculation_log.csv), ratio summaries, and performance metrics.
"""

import math
import time
import csv
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd

from src.utils.logger import get_logger
from src.config.settings import BASE_DIR
from src.config.ratio_config import (
    OPM_TOLERANCE,
    ROE_BENCHMARKS,
    ROCE_BENCHMARKS,
    ROA_BENCHMARKS,
    NPM_BENCHMARKS,
    OPM_BENCHMARKS,
    DEFAULT_PRECISION
)
from src.analytics.ratio_base import RatioCalculator, RatioResult

# Setup dedicated ratio logger
def _setup_ratio_logger() -> logging.Logger:
    logger = logging.getLogger("ratio_engine")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        log_dir = BASE_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "ratio_engine.log"
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

ratio_logger = _setup_ratio_logger()


def safe_divide(numerator: Any, denominator: Any, multiplier: float = 1.0, precision: int = DEFAULT_PRECISION) -> Optional[float]:
    val, _ = RatioCalculator.safe_divide(numerator, denominator, multiplier=multiplier, precision=precision)
    return val


def calculate_net_profit_margin(net_profit: Any, sales: Any, precision: int = DEFAULT_PRECISION) -> Optional[float]:
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
    precision: int = DEFAULT_PRECISION
) -> Optional[float]:
    try:
        if float(sales) <= 0:
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
                        f"OPM mismatch for {company_id} ({year}): Expected {rep_opm_val:.2f}%, Computed {computed_opm:.2f}% (diff={diff:.2f}%)"
                    )
                else:
                    ratio_logger.info(f"OPM cross-check matched for {company_id} ({year}): {computed_opm:.2f}%")
        except (ValueError, TypeError):
            pass

    return computed_opm


def calculate_roe(net_profit: Any, equity_capital: Any, reserves: Any, precision: int = DEFAULT_PRECISION) -> Optional[float]:
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
    precision: int = DEFAULT_PRECISION
) -> Optional[float]:
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

    return safe_divide(ebit_or_op, capital_employed, multiplier=100.0, precision=precision)


def calculate_roa(net_profit: Any, total_assets: Any, precision: int = DEFAULT_PRECISION) -> Optional[float]:
    try:
        if float(total_assets) <= 0:
            return None
    except (ValueError, TypeError):
        return None

    return safe_divide(net_profit, total_assets, multiplier=100.0, precision=precision)


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
        is_financial: bool = False
    ) -> List[RatioResult]:
        results: List[RatioResult] = []

        # 1. NPM
        val_npm, status_npm = cls.safe_divide(net_profit, sales, multiplier=100.0)
        if sales is not None and float(sales or 0) <= 0:
            status_npm = "NON_POSITIVE_SALES"
            val_npm = None
        results.append(
            cls.create_result(company_id, year, "NPM", val_npm, status_npm, "Net Profit / Sales * 100", "profitandloss", NPM_BENCHMARKS)
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
                    ratio_logger.warning(f"OPM mismatch for {company_id} ({year}): Expected {reported_opm}%, Computed {val_opm:.2f}%")
            except (ValueError, TypeError):
                pass
        results.append(
            cls.create_result(company_id, year, "OPM", val_opm, status_opm, "Operating Profit / Sales * 100", "profitandloss", OPM_BENCHMARKS)
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
            cls.create_result(company_id, year, "ROE", val_roe, status_roe, "PAT / (Equity + Reserves) * 100", "profitandloss + balancesheet", ROE_BENCHMARKS)
        )

        # 4. ROCE
        borr = float(borrowings or 0)
        cap_emp = tot_eq + borr
        val_roce, status_roce = cls.safe_divide(operating_profit, cap_emp, multiplier=100.0)
        if cap_emp <= 0:
            status_roce = "NON_POSITIVE_CAPITAL_EMPLOYED"
            val_roce = None
        if is_financial:
            ratio_logger.info(f"ROCE calculated for financial entity {company_id} ({year})")
        results.append(
            cls.create_result(company_id, year, "ROCE", val_roce, status_roce, "EBIT / Capital Employed * 100", "profitandloss + balancesheet", ROCE_BENCHMARKS)
        )

        # 5. ROA
        val_roa, status_roa = cls.safe_divide(net_profit, total_assets, multiplier=100.0)
        if total_assets is not None and float(total_assets or 0) <= 0:
            status_roa = "NON_POSITIVE_ASSETS"
            val_roa = None
        results.append(
            cls.create_result(company_id, year, "ROA", val_roa, status_roa, "PAT / Total Assets * 100", "profitandloss + balancesheet", ROA_BENCHMARKS)
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
        is_financial: bool = False
    ) -> Dict[str, Optional[float]]:
        """Legacy compatibility wrapper returning dictionary of ratio values."""
        rlist = cls.compute_period_ratios(
            company_id, year, sales, operating_profit, net_profit, equity_capital, reserves, borrowings, total_assets, reported_opm, is_financial
        )
        res_map = {r.ratio_name.lower(): r.value for r in rlist}
        res_map["company_id"] = company_id
        res_map["year"] = year
        return res_map

    @classmethod
    def export_ratio_audit_and_summary(cls, results: List[RatioResult], output_dir: Optional[Path] = None):
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
            summary_rows.append({
                "KPI": ratio_name,
                "Total_Evaluated": len(sub),
                "Valid_Count": len(vals),
                "Null_Count": len(sub) - len(vals),
                "Average": round(vals.mean(), 2) if not vals.empty else None,
                "Min": round(vals.min(), 2) if not vals.empty else None,
                "Max": round(vals.max(), 2) if not vals.empty else None,
            })
        df_summary = pd.DataFrame(summary_rows)
        df_summary.to_csv(summary_file, index=False)
        ratio_logger.info(f"Exported ratio summary statistics to {summary_file}")
