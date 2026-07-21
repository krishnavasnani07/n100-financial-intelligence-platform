"""
Cash Flow Analytics Engine for Nifty 100 Financial Intelligence Platform.
Computes Free Cash Flow (FCF), CFO Quality Score, CapEx Intensity, FCF Conversion,
and Capital Allocation Classification.
"""

import math
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd

from src.utils.logger import get_logger
from src.config.settings import BASE_DIR
from src.config.cashflow_config import (
    DEFAULT_CASHFLOW_PRECISION,
    CFO_QUALITY_HIGH_THRESHOLD,
    CFO_QUALITY_MODERATE_THRESHOLD,
    LABEL_CFO_HIGH,
    LABEL_CFO_MODERATE,
    LABEL_CFO_ACCRUAL_RISK,
    CAPEX_ASSET_LIGHT_THRESHOLD,
    CAPEX_INTENSIVE_THRESHOLD,
    LABEL_CAPEX_ASSET_LIGHT,
    LABEL_CAPEX_MODERATE,
    LABEL_CAPEX_INTENSIVE,
    PATTERN_MAP,
    LABEL_SHAREHOLDER_RETURNS
)
from src.analytics.ratio_base import RatioCalculator


# Setup ratio logger (logs/ratio_engine.log)
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


# Reusable Utility Functions (Phase 4)
def safe_divide(
    numerator: Any,
    denominator: Any,
    multiplier: float = 1.0,
    precision: int = DEFAULT_CASHFLOW_PRECISION
) -> Optional[float]:
    """Safe division helper handling zero, None, and non-numeric types."""
    val, _ = RatioCalculator.safe_divide(numerator, denominator, multiplier=multiplier, precision=precision)
    return val


def get_sign(value: Any) -> str:
    """Returns '+' if value > 0 else '-'."""
    try:
        val = float(value)
        return "+" if val > 0 else "-"
    except (ValueError, TypeError):
        return "-"


def average_last_n_years(values: List[float], n: int = 5) -> Optional[float]:
    """Computes the average of non-None float values over the last n years."""
    clean_vals = [v for v in values if v is not None and not math.isnan(v)]
    if not clean_vals:
        return None
    recent_vals = clean_vals[-n:]
    return round(sum(recent_vals) / len(recent_vals), DEFAULT_CASHFLOW_PRECISION)


def classify_cfo_quality(ratio: Optional[float]) -> Optional[str]:
    """Classifies CFO Quality ratio into High, Moderate, or Accrual Risk."""
    if ratio is None:
        return None
    if ratio > CFO_QUALITY_HIGH_THRESHOLD:
        return LABEL_CFO_HIGH
    elif ratio >= CFO_QUALITY_MODERATE_THRESHOLD:
        return LABEL_CFO_MODERATE
    else:
        return LABEL_CFO_ACCRUAL_RISK


def classify_capex_intensity(percentage: Optional[float]) -> Optional[str]:
    """Classifies CapEx Intensity percentage into Asset Light, Moderate, or Capital Intensive."""
    if percentage is None:
        return None
    if percentage < CAPEX_ASSET_LIGHT_THRESHOLD:
        return LABEL_CAPEX_ASSET_LIGHT
    elif percentage <= CAPEX_INTENSIVE_THRESHOLD:
        return LABEL_CAPEX_MODERATE
    else:
        return LABEL_CAPEX_INTENSIVE


# Standalone KPI Calculations (Phase 5 - Phase 8)
def calculate_free_cash_flow(
    operating_activity: Any,
    investing_activity: Any,
    precision: int = DEFAULT_CASHFLOW_PRECISION,
    company_id: str = "UNKNOWN",
    year: str = "UNKNOWN"
) -> Optional[float]:
    """
    Computes Free Cash Flow (FCF) = Operating Cash Flow + Investing Cash Flow.
    Investing Cash Flow is typically negative. Negative FCF is valid.
    """
    try:
        cfo = float(operating_activity) if operating_activity is not None else 0.0
        cfi = float(investing_activity) if investing_activity is not None else 0.0
        fcf = round(cfo + cfi, precision)
        ratio_logger.info(f"Computed Free Cash Flow {company_id} {year} ₹{fcf:g} Cr")
        return fcf
    except (ValueError, TypeError):
        return None


def calculate_cfo_quality(
    operating_activity: Any,
    net_profit: Any,
    precision: int = DEFAULT_CASHFLOW_PRECISION,
    company_id: str = "UNKNOWN",
    year: str = "UNKNOWN"
) -> Optional[float]:
    """
    Computes single-period CFO Quality ratio = Operating Cash Flow / Net Profit (PAT).
    Returns None if Net Profit is 0 or negative/invalid.
    """
    try:
        pat = float(net_profit) if net_profit is not None else 0.0
        if pat <= 0:
            ratio_logger.warning(f"PAT = 0 Skipped CFO Quality for {company_id} ({year})")
            return None
    except (ValueError, TypeError):
        ratio_logger.warning(f"PAT = 0 Skipped CFO Quality for {company_id} ({year})")
        return None

    return safe_divide(operating_activity, pat, multiplier=1.0, precision=precision)


def calculate_capex_intensity(
    investing_activity: Any,
    sales: Any,
    precision: int = DEFAULT_CASHFLOW_PRECISION,
    company_id: str = "UNKNOWN",
    year: str = "UNKNOWN"
) -> Optional[float]:
    """
    Computes CapEx Intensity (%) = ABS(Investing Cash Flow) / Sales * 100.
    Returns None if Sales <= 0 or invalid.
    """
    try:
        s = float(sales) if sales is not None else 0.0
        if s <= 0:
            ratio_logger.warning(f"Sales = 0 Skipped CapEx Intensity for {company_id} ({year})")
            return None
        cfi = float(investing_activity) if investing_activity is not None else 0.0
        return safe_divide(abs(cfi), s, multiplier=100.0, precision=precision)
    except (ValueError, TypeError):
        return None


def calculate_fcf_conversion(
    free_cash_flow: Any,
    operating_profit: Any,
    precision: int = DEFAULT_CASHFLOW_PRECISION,
    company_id: str = "UNKNOWN",
    year: str = "UNKNOWN"
) -> Optional[float]:
    """
    Computes FCF Conversion = Free Cash Flow / Operating Profit.
    Returns None if Operating Profit <= 0 or invalid.
    """
    try:
        op = float(operating_profit) if operating_profit is not None else 0.0
        if op <= 0:
            ratio_logger.info(f"Zero Operating Profit Skipped FCF Conversion for {company_id} ({year})")
            return None
        fcf = float(free_cash_flow) if free_cash_flow is not None else 0.0
        return safe_divide(fcf, op, multiplier=1.0, precision=precision)
    except (ValueError, TypeError):
        return None


def classify_capital_allocation(
    cfo: Any,
    cfi: Any,
    cff: Any,
    cfo_pat_ratio: Optional[float] = None,
    company_id: str = "UNKNOWN",
    year: str = "UNKNOWN"
) -> Tuple[str, str, str, str]:
    """
    Classifies company capital allocation into one of 8 patterns based on cash flow signs.
    Special case (+, -, -): Shareholder Returns if CFO/PAT > 1.0, else Reinvestor.
    """
    cfo_sign = get_sign(cfo)
    cfi_sign = get_sign(cfi)
    cff_sign = get_sign(cff)
    key = (cfo_sign, cfi_sign, cff_sign)

    if key == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > CFO_QUALITY_HIGH_THRESHOLD:
            label = LABEL_SHAREHOLDER_RETURNS
        else:
            label = PATTERN_MAP[key]
    else:
        label = PATTERN_MAP.get(key, "Mixed")

    ratio_logger.info(f"Capital Allocation {company_id} Pattern {label}")
    return cfo_sign, cfi_sign, cff_sign, label


# Engine Class (Phase 9 & Phase 10)
class CashFlowEngine:
    """
    Cash Flow Intelligence Engine.
    Executes FCF, CFO Quality, CapEx Intensity, FCF Conversion, and Pattern Classification.
    Generates capital_allocation.csv, cashflow_summary.csv, and pattern statistics.
    """

    @classmethod
    def compute_period_kpis(
        cls,
        company_id: str,
        year: str,
        operating_activity: Any,
        investing_activity: Any,
        financing_activity: Any,
        sales: Any,
        operating_profit: Any,
        net_profit: Any,
        cfo_pat_5yr_avg: Optional[float] = None
    ) -> Dict[str, Any]:
        """Computes all Cash Flow KPIs and Capital Allocation Pattern for a single period."""
        fcf = calculate_free_cash_flow(operating_activity, investing_activity, company_id=company_id, year=year)
        cfo_qual_period = calculate_cfo_quality(operating_activity, net_profit, company_id=company_id, year=year)
        
        # Effective CFO quality for pattern classifier: preference given to 5yr avg if available
        eff_cfo_pat = cfo_pat_5yr_avg if cfo_pat_5yr_avg is not None else cfo_qual_period
        cfo_qual_label = classify_cfo_quality(eff_cfo_pat)

        capex_pct = calculate_capex_intensity(investing_activity, sales, company_id=company_id, year=year)
        capex_label = classify_capex_intensity(capex_pct)

        fcf_conv = calculate_fcf_conversion(fcf, operating_profit, company_id=company_id, year=year)

        cfo_sign, cfi_sign, cff_sign, pattern_label = classify_capital_allocation(
            cfo=operating_activity,
            cfi=investing_activity,
            cff=financing_activity,
            cfo_pat_ratio=eff_cfo_pat,
            company_id=company_id,
            year=year
        )

        return {
            "company_id": company_id,
            "year": str(year),
            "free_cash_flow": fcf,
            "cfo_quality_period": cfo_qual_period,
            "cfo_quality_5yr_avg": cfo_pat_5yr_avg,
            "cfo_quality_label": cfo_qual_label,
            "capex_intensity_pct": capex_pct,
            "capex_intensity_label": capex_label,
            "fcf_conversion": fcf_conv,
            "cfo_sign": cfo_sign,
            "cfi_sign": cfi_sign,
            "cff_sign": cff_sign,
            "pattern_label": pattern_label
        }

    @classmethod
    def compute_company_cashflow_kpis(
        cls,
        company_id: str,
        df_company: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Computes Cash Flow KPIs for all available years for a single company,
        including 5-year rolling CFO Quality averages.
        """
        df_sorted = df_company.sort_values(by="year").copy()
        
        # Pre-calculate period CFO Quality ratios to get 5-year rolling averages
        cfo_qualities = []
        for _, row in df_sorted.iterrows():
            q = calculate_cfo_quality(row.get("operating_activity"), row.get("net_profit"), company_id=company_id, year=row.get("year"))
            cfo_qualities.append(q)

        results = []
        for i, (_, row) in enumerate(df_sorted.iterrows()):
            # Available history up to index i (up to 5 years)
            hist_q = cfo_qualities[max(0, i - 4): i + 1]
            avg_5yr = average_last_n_years(hist_q, n=5)

            res = cls.compute_period_kpis(
                company_id=company_id,
                year=row.get("year"),
                operating_activity=row.get("operating_activity"),
                investing_activity=row.get("investing_activity"),
                financing_activity=row.get("financing_activity"),
                sales=row.get("sales"),
                operating_profit=row.get("operating_profit"),
                net_profit=row.get("net_profit"),
                cfo_pat_5yr_avg=avg_5yr
            )
            results.append(res)

        return results

    @classmethod
    def export_cashflow_reports(
        cls,
        results: List[Dict[str, Any]],
        output_dir: Optional[Path] = None
    ) -> Dict[str, Path]:
        """
        Exports:
        1. capital_allocation.csv (company_id, year, cfo_sign, cfi_sign, cff_sign, pattern_label)
        2. cashflow_summary.csv (full KPI summary)
        3. capital_pattern_statistics.csv (pattern frequency distribution)
        """
        out_dir = output_dir or (BASE_DIR / "output")
        out_dir.mkdir(parents=True, exist_ok=True)
        df_all = pd.DataFrame(results)

        # 1. capital_allocation.csv
        file_cap_alloc = out_dir / "capital_allocation.csv"
        alloc_cols = ["company_id", "year", "cfo_sign", "cfi_sign", "cff_sign", "pattern_label"]
        df_alloc = df_all[alloc_cols] if not df_all.empty else pd.DataFrame(columns=alloc_cols)
        df_alloc.to_csv(file_cap_alloc, index=False)
        ratio_logger.info(f"Generated capital allocation report at {file_cap_alloc}")

        # 2. cashflow_summary.csv
        file_summary = out_dir / "cashflow_summary.csv"
        df_all.to_csv(file_summary, index=False)
        ratio_logger.info(f"Generated cash flow summary report at {file_summary}")

        # 3. capital_pattern_statistics.csv
        file_stats = out_dir / "capital_pattern_statistics.csv"
        if not df_all.empty and "pattern_label" in df_all.columns:
            counts = df_all["pattern_label"].value_counts().reset_index()
            counts.columns = ["pattern_label", "count"]
            counts["percentage"] = (counts["count"] / len(df_all) * 100).round(2)
        else:
            counts = pd.DataFrame(columns=["pattern_label", "count", "percentage"])
        counts.to_csv(file_stats, index=False)
        ratio_logger.info(f"Generated pattern statistics report at {file_stats}")

        return {
            "capital_allocation": file_cap_alloc,
            "cashflow_summary": file_summary,
            "pattern_statistics": file_stats
        }
