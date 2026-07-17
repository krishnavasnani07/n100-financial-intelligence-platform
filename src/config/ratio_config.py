"""
Ratio Engine Configuration & Benchmark Standards (Sprint 2).
Centralizes thresholds, tolerances, formula versions, and benchmark classifications.
"""

from typing import Dict

# Formula Version
FORMULA_VERSION = "1.0"

# Numerical Precision & Tolerances
DEFAULT_PRECISION = 2
OPM_TOLERANCE = 1.0  # Percentage point tolerance for OPM cross-check

# Performance Thresholds for Classification
ROE_BENCHMARKS: Dict[str, float] = {
    "EXCELLENT": 20.0,
    "GOOD": 15.0,
    "AVERAGE": 10.0,
}

ROCE_BENCHMARKS: Dict[str, float] = {
    "EXCELLENT": 20.0,
    "GOOD": 15.0,
    "AVERAGE": 10.0,
}

ROA_BENCHMARKS: Dict[str, float] = {
    "EXCELLENT": 15.0,
    "GOOD": 10.0,
    "AVERAGE": 5.0,
}

NPM_BENCHMARKS: Dict[str, float] = {
    "EXCELLENT": 15.0,
    "GOOD": 10.0,
    "AVERAGE": 5.0,
}

OPM_BENCHMARKS: Dict[str, float] = {
    "EXCELLENT": 25.0,
    "GOOD": 15.0,
    "AVERAGE": 10.0,
}
