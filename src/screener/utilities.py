"""
Utility functions for Screener Engine.
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd


def coerce_float(value: Any) -> Optional[float]:
    """Safely coerce any value to a float or return None."""
    if value is None:
        return None
    try:
        if isinstance(value, str) and value.strip() == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def get_series(frame: pd.DataFrame, aliases: list[str]) -> Optional[pd.Series]:
    """Finds and returns the first matching column series from a list of aliases."""
    for alias in aliases:
        if alias in frame.columns:
            return frame[alias]
    return None
