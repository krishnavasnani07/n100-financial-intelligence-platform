"""
Generic Ratio Base Class & Data Models (Sprint 2).
Provides reusable division, validation, benchmarking, and structured RatioResult models.
"""

import math
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Any, Optional, Dict, List
from src.config.ratio_config import DEFAULT_PRECISION, FORMULA_VERSION

@dataclass
class RatioResult:
    """Structured result object for calculated KPIs."""
    company_id: str
    year: str
    ratio_name: str
    value: Optional[float]
    status: str  # VALID, NULL_DENOMINATOR, NEGATIVE_DENOMINATOR, INVALID_INPUT
    formula: str
    source_tables: str
    classification: str  # EXCELLENT, GOOD, AVERAGE, WEAK, N/A
    formula_version: str = FORMULA_VERSION
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RatioCalculator:
    """
    Base utility class for all KPI ratio computations across analytics engines.
    """

    @staticmethod
    def safe_divide(
        numerator: Any,
        denominator: Any,
        multiplier: float = 1.0,
        precision: int = DEFAULT_PRECISION
    ) -> tuple[Optional[float], str]:
        """
        Safely divide two values with multiplier and return (value, status_code).
        """
        if numerator is None or denominator is None:
            return None, "NULL_INPUT"

        try:
            num = float(numerator)
            den = float(denominator)

            if math.isnan(num) or math.isnan(den) or math.isinf(num) or math.isinf(den):
                return None, "INVALID_INPUT"

            if den == 0.0:
                return None, "NULL_DENOMINATOR"

            if den < 0.0:
                return None, "NEGATIVE_DENOMINATOR"

            res = round((num / den) * multiplier, precision)
            return res, "VALID"

        except (ValueError, TypeError, OverflowError):
            return None, "TYPE_ERROR"

    @staticmethod
    def classify_benchmark(value: Optional[float], benchmarks: Dict[str, float]) -> str:
        """Classify ratio value into performance buckets."""
        if value is None:
            return "N/A"

        if value >= benchmarks.get("EXCELLENT", 20.0):
            return "EXCELLENT"
        elif value >= benchmarks.get("GOOD", 15.0):
            return "GOOD"
        elif value >= benchmarks.get("AVERAGE", 10.0):
            return "AVERAGE"
        else:
            return "WEAK"

    @classmethod
    def create_result(
        cls,
        company_id: str,
        year: str,
        ratio_name: str,
        value: Optional[float],
        status: str,
        formula: str,
        source_tables: str,
        benchmarks: Optional[Dict[str, float]] = None
    ) -> RatioResult:
        classification = cls.classify_benchmark(value, benchmarks) if benchmarks else "N/A"
        return RatioResult(
            company_id=company_id,
            year=year,
            ratio_name=ratio_name,
            value=value,
            status=status,
            formula=formula,
            source_tables=source_tables,
            classification=classification
        )
