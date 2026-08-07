"""
Growth Analytics Engine - Compound Annual Growth Rate (CAGR) Engine.

Provides a reusable CAGR engine to compute Revenue, PAT, and EPS growth
across 3-year, 5-year, and 10-year windows while handling financial edge cases gracefully:
1. Positive -> Positive: Returns calculated CAGR (%) with status VALID.
2. Positive -> Negative / Zero: Returns None with status DECLINE_TO_LOSS.
3. Negative -> Positive: Returns None with status TURNAROUND.
4. Negative -> Negative / Zero: Returns None with status BOTH_NEGATIVE.
5. Zero Base: Returns None with status ZERO_BASE.
6. Insufficient Data / Years: Returns None with status INSUFFICIENT.
"""

import logging
import math
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.analytics.ratio_base import RatioCalculator
from src.config.growth_config import (CAGR_METRICS, CAGR_TIME_WINDOWS,
                                      DEFAULT_CAGR_PRECISION,
                                      FLAG_BOTH_NEGATIVE, FLAG_DECLINE_TO_LOSS,
                                      FLAG_INSUFFICIENT, FLAG_INVALID_INPUT,
                                      FLAG_TURNAROUND, FLAG_VALID,
                                      FLAG_ZERO_BASE,
                                      GROWTH_CLASSIFICATION_THRESHOLDS,
                                      LABEL_DECLINING, LABEL_HIGH_GROWTH,
                                      LABEL_MODERATE_GROWTH,
                                      LABEL_NOT_APPLICABLE, LABEL_SLOW_GROWTH,
                                      LABEL_STRONG_GROWTH)
from src.config.settings import BASE_DIR
from src.utils.helpers import extract_year_int
from src.utils.logger import get_logger

ratio_logger = get_logger("ratio_engine")


def calculate_cagr(
    start_value: Any,
    end_value: Any,
    years: int,
    precision: int = DEFAULT_CAGR_PRECISION,
    company_id: str = "UNKNOWN",
    metric_name: str = "Metric",
) -> Tuple[Optional[float], str]:
    """
    Generic, reusable CAGR engine.

    Formula:
        CAGR = ((End / Start) ^ (1 / Years) - 1) * 100

    Handles all 6 financial edge cases:
        1. Positive -> Positive (Returns CAGR %, FLAG_VALID)
        2. Positive -> Negative / Zero (Returns None, FLAG_DECLINE_TO_LOSS)
        3. Negative -> Positive (Returns None, FLAG_TURNAROUND)
        4. Negative -> Negative / Zero (Returns None, FLAG_BOTH_NEGATIVE)
        5. Zero Base (Returns None, FLAG_ZERO_BASE)
        6. Insufficient Data / Invalid Years (Returns None, FLAG_INSUFFICIENT)

    Parameters:
        start_value (Any): The initial value.
        end_value (Any): The final value.
        years (int): The number of years/periods.
        precision (int): Number of decimal places to round to.
        company_id (str): ID of the company (for logging).
        metric_name (str): Name of the metric being calculated.

    Returns:
        Tuple[Optional[float], str]: (CAGR value or None, Flag status string)
    """
    # Case 6: Check for missing inputs or non-positive years
    if years is None or not isinstance(years, (int, float)) or years <= 0:
        ratio_logger.warning(
            f"INSUFFICIENT years for {metric_name} CAGR ({company_id}): years={years}"
        )
        return None, FLAG_INSUFFICIENT

    if start_value is None or end_value is None:
        ratio_logger.warning(
            f"INSUFFICIENT data for {metric_name} CAGR ({company_id}): start={start_value}, end={end_value}"
        )
        return None, FLAG_INSUFFICIENT

    try:
        start_val = float(start_value)
        end_val = float(end_value)
    except (ValueError, TypeError):
        ratio_logger.warning(
            f"INVALID_INPUT data types for {metric_name} CAGR ({company_id}): start={start_value}, end={end_value}"
        )
        return None, FLAG_INVALID_INPUT

    if (
        math.isnan(start_val)
        or math.isnan(end_val)
        or math.isinf(start_val)
        or math.isinf(end_val)
    ):
        ratio_logger.warning(
            f"INVALID_INPUT NaN/Inf values for {metric_name} CAGR ({company_id})"
        )
        return None, FLAG_INVALID_INPUT

    # Case 5: Zero Base
    if start_val == 0.0:
        ratio_logger.warning(
            f"ZERO_BASE {metric_name} CAGR skipped for {company_id}: start=0.0, end={end_val}"
        )
        return None, FLAG_ZERO_BASE

    # Case 2: Positive -> Negative / Zero (Decline to Loss)
    if start_val > 0.0 and end_val <= 0.0:
        ratio_logger.warning(
            f"DECLINE_TO_LOSS {metric_name} CAGR skipped for {company_id}: start={start_val}, end={end_val}"
        )
        return None, FLAG_DECLINE_TO_LOSS

    # Case 3: Negative -> Positive (Turnaround)
    if start_val < 0.0 and end_val > 0.0:
        ratio_logger.warning(
            f"TURNAROUND {metric_name} CAGR skipped for {company_id}: start={start_val}, end={end_val}"
        )
        return None, FLAG_TURNAROUND

    # Case 4: Negative -> Negative / Zero (Both Negative)
    if start_val < 0.0 and end_val <= 0.0:
        ratio_logger.warning(
            f"BOTH_NEGATIVE {metric_name} CAGR skipped for {company_id}: start={start_val}, end={end_val}"
        )
        return None, FLAG_BOTH_NEGATIVE

    # Case 1: Positive -> Positive
    if start_val > 0.0 and end_val > 0.0:
        if start_val == end_val:
            cagr = 0.0
        else:
            cagr = ((end_val / start_val) ** (1.0 / years) - 1.0) * 100.0
        cagr_rounded = round(cagr, precision)
        ratio_logger.info(
            f"{metric_name} CAGR {company_id} {years}Y {cagr_rounded:.2f}%"
        )
        return cagr_rounded, FLAG_VALID

    return None, FLAG_INVALID_INPUT


def classify_growth_cagr(cagr_val: Optional[float], flag: str = FLAG_VALID) -> str:
    """
    Classify growth rate into discrete business performance tiers.

    Tiers:
        > 20%: High Growth
        10% - 20%: Strong Growth
        5% - 10%: Moderate
        0% - 5%: Slow
        < 0%: Declining
        None / Edge Case: N/A

    Parameters:
        cagr_val (Optional[float]): CAGR value.
        flag (str): Flag status of the CAGR calculation.

    Returns:
        str: Growth tier classification label.
    """
    if cagr_val is None or flag != FLAG_VALID:
        return LABEL_NOT_APPLICABLE

    if cagr_val > GROWTH_CLASSIFICATION_THRESHOLDS["HIGH_GROWTH"]:
        return LABEL_HIGH_GROWTH
    elif cagr_val >= GROWTH_CLASSIFICATION_THRESHOLDS["STRONG_GROWTH"]:
        return LABEL_STRONG_GROWTH
    elif cagr_val >= GROWTH_CLASSIFICATION_THRESHOLDS["MODERATE_GROWTH"]:
        return LABEL_MODERATE_GROWTH
    elif cagr_val >= GROWTH_CLASSIFICATION_THRESHOLDS["SLOW_GROWTH"]:
        return LABEL_SLOW_GROWTH
    else:
        return LABEL_DECLINING


@dataclass
class CAGRResult:
    """Structured data model for CAGR calculation results."""

    company_id: str
    metric_name: str
    period_years: int
    start_year: str
    end_year: str
    start_value: Optional[float]
    end_value: Optional[float]
    cagr: Optional[float]
    flag: str
    growth_label: str
    formula_version: str = "1.0.0"
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CAGREngine(RatioCalculator):
    """
    Growth Analytics Engine for multi-year CAGR calculations across companies.
    Reuses calculate_cagr() engine to compute Revenue, PAT, and EPS CAGR over 3Y, 5Y, and 10Y.
    """

    @classmethod
    def compute_single_cagr(
        cls,
        company_id: str,
        metric_name: str,
        period_years: int,
        start_year: str,
        end_year: str,
        start_value: Any,
        end_value: Any,
        precision: int = DEFAULT_CAGR_PRECISION,
    ) -> CAGRResult:
        """
        Computes CAGR for a single metric & period window, returning a CAGRResult object.

        Parameters:
            company_id (str): ID of the company.
            metric_name (str): Name of the metric.
            period_years (int): Number of years.
            start_year (str): Starting year label.
            end_year (str): Ending year label.
            start_value (Any): Starting value.
            end_value (Any): Ending value.
            precision (int): Rounding precision.

        Returns:
            CAGRResult: Structured result object.
        """
        cagr_val, flag = calculate_cagr(
            start_value=start_value,
            end_value=end_value,
            years=period_years,
            precision=precision,
            company_id=company_id,
            metric_name=f"{metric_name}_{period_years}Y",
        )

        growth_label = classify_growth_cagr(cagr_val, flag=flag)

        start_val_clean = (
            float(start_value)
            if start_value is not None and not math.isnan(float(start_value or 0))
            else None
        )
        end_val_clean = (
            float(end_value)
            if end_value is not None and not math.isnan(float(end_value or 0))
            else None
        )

        return CAGRResult(
            company_id=company_id,
            metric_name=metric_name,
            period_years=period_years,
            start_year=start_year,
            end_year=end_year,
            start_value=start_val_clean,
            end_value=end_val_clean,
            cagr=cagr_val,
            flag=flag,
            growth_label=growth_label,
        )

    @classmethod
    def compute_company_cagr(
        cls,
        company_id: str,
        df_history: pd.DataFrame,
        windows: List[int] = CAGR_TIME_WINDOWS,
        metrics: Dict[str, str] = CAGR_METRICS,
    ) -> List[CAGRResult]:
        """
        Given historical annual financial records for a company (DataFrame with columns: year, sales, net_profit, eps),
        computes CAGR for all metrics across specified time windows (3Y, 5Y, 10Y).

        Parameters:
            company_id (str): ID of the company.
            df_history (pd.DataFrame): Dataframe of historical financial records.
            windows (List[int]): List of CAGR time windows to compute.
            metrics (Dict[str, str]): Mapping of column names to display names.

        Returns:
            List[CAGRResult]: List of calculated CAGR result objects.
        """
        results: List[CAGRResult] = []

        if df_history is None or df_history.empty:
            ratio_logger.warning(
                f"No historical data provided for company {company_id}"
            )
            return results

        # Clean & parse numerical years, filtering out 'TTM'
        df_clean = df_history[
            df_history["year"].astype(str).str.upper() != "TTM"
        ].copy()

        df_clean["year_int"] = df_clean["year"].apply(extract_year_int)
        df_clean = (
            df_clean.dropna(subset=["year_int"])
            .sort_values("year_int")
            .drop_duplicates(subset=["year_int"], keep="last")
        )

        if df_clean.empty:
            ratio_logger.warning(
                f"Insufficient annual records for company {company_id}"
            )
            return results

        # Create lookup dictionary mapping year_int -> row
        year_map = {row["year_int"]: row for _, row in df_clean.iterrows()}
        all_years = sorted(year_map.keys())
        latest_year = all_years[-1]

        latest_row = year_map[latest_year]
        end_year_str = str(latest_row["year"])

        for col_name, display_name in metrics.items():
            for window in windows:
                target_start_year = latest_year - window
                if target_start_year in year_map:
                    start_row = year_map[target_start_year]
                    start_year_str = str(start_row["year"])
                    start_val = start_row.get(col_name)
                    end_val = latest_row.get(col_name)

                    res = cls.compute_single_cagr(
                        company_id=company_id,
                        metric_name=display_name,
                        period_years=window,
                        start_year=start_year_str,
                        end_year=end_year_str,
                        start_value=start_val,
                        end_value=end_val,
                    )
                else:
                    # Target start year missing
                    res = CAGRResult(
                        company_id=company_id,
                        metric_name=display_name,
                        period_years=window,
                        start_year=str(target_start_year),
                        end_year=end_year_str,
                        start_value=None,
                        end_value=(
                            float(latest_row.get(col_name, 0.0))
                            if latest_row.get(col_name) is not None
                            else None
                        ),
                        cagr=None,
                        flag=FLAG_INSUFFICIENT,
                        growth_label=LABEL_NOT_APPLICABLE,
                    )
                    ratio_logger.warning(
                        f"INSUFFICIENT history for {company_id} {display_name} {window}Y: missing year {target_start_year}"
                    )

                results.append(res)

        return results

    @classmethod
    def export_growth_reports(
        cls, results: List[CAGRResult], output_dir: Optional[Path] = None
    ):
        """
        Generates output/growth_summary.csv and output/cagr_statistics.csv.

        Parameters:
            results (List[CAGRResult]): List of CAGR results.
            output_dir (Optional[Path]): Custom output directory.
        """
        out_dir = output_dir or (BASE_DIR / "output")
        out_dir.mkdir(parents=True, exist_ok=True)

        if not results:
            ratio_logger.warning(
                "No CAGR results provided for exporting growth reports."
            )
            return

        df_raw = pd.DataFrame([r.to_dict() for r in results])

        # 1. Generate cagr_statistics.csv
        flag_counts = df_raw["flag"].value_counts().to_dict()
        all_flags = [
            FLAG_VALID,
            FLAG_DECLINE_TO_LOSS,
            FLAG_TURNAROUND,
            FLAG_BOTH_NEGATIVE,
            FLAG_ZERO_BASE,
            FLAG_INSUFFICIENT,
            FLAG_INVALID_INPUT,
        ]
        stat_rows = [
            {"Flag": flag, "Count": flag_counts.get(flag, 0)} for flag in all_flags
        ]
        df_stats = pd.DataFrame(stat_rows)
        stats_path = out_dir / "cagr_statistics.csv"
        df_stats.to_csv(stats_path, index=False)
        ratio_logger.info(f"Exported CAGR flag statistics report to {stats_path}")

        # 2. Generate growth_summary.csv (Pivot per company)
        summary_rows = []
        companies = df_raw["company_id"].unique()

        for cid in sorted(companies):
            comp_df = df_raw[df_raw["company_id"] == cid]
            row_dict = {"Company": cid}

            # Map metrics: Revenue_3Y, Revenue_5Y, Revenue_10Y, PAT_3Y, etc.
            rev_5y_cagr = None
            for _, r in comp_df.iterrows():
                key = f"{r['metric_name']}_{r['period_years']}Y"
                row_dict[key] = r["cagr"] if r["flag"] == FLAG_VALID else None
                row_dict[f"{key}_Flag"] = r["flag"]
                if r["metric_name"] == "Revenue" and r["period_years"] == 5:
                    rev_5y_cagr = r["cagr"]

            # Set overall Company Growth Label based on 5Y Revenue CAGR (or 3Y if 5Y not valid)
            rev_3y_cagr = row_dict.get("Revenue_3Y")
            primary_cagr = rev_5y_cagr if rev_5y_cagr is not None else rev_3y_cagr
            row_dict["Growth_Label"] = classify_growth_cagr(
                primary_cagr,
                FLAG_VALID if primary_cagr is not None else FLAG_INSUFFICIENT,
            )

            summary_rows.append(row_dict)

        df_summary = pd.DataFrame(summary_rows)
        summary_path = out_dir / "growth_summary.csv"
        df_summary.to_csv(summary_path, index=False)
        ratio_logger.info(f"Exported Growth Summary report to {summary_path}")
