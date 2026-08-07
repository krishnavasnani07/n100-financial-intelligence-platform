import re
from pathlib import Path
from typing import Any, List, Optional

import pandas as pd

from src.config import settings


def list_raw_excel_files() -> List[Path]:
    """
    Returns a sorted list of all Excel files (.xlsx and .xls) in the raw data directory.

    Returns:
        List[Path]: List of Paths to the Excel files found.
    """
    raw_dir = Path(settings.RAW_DATA_DIR)
    if not raw_dir.exists():
        return []
    # Combine both xlsx and xls file matches
    files = list(raw_dir.glob("*.xlsx")) + list(raw_dir.glob("*.xls"))
    return sorted(files)


def extract_year_int(yr_val: Any) -> Optional[int]:
    """
    Extracts a 4-digit calendar year integer from a year string or integer.
    Returns None for TTM or invalid/empty values.
    """
    if not yr_val or pd.isnull(yr_val):
        return None
    val_str = str(yr_val).strip()
    if val_str.upper() == "TTM":
        return None
    m = re.search(r"\b(19\d\d|20\d\d)\b", val_str)
    return int(m.group(1)) if m else None


def map_year_to_price_date(year_str: str) -> Optional[str]:
    """
    Maps financial year strings to stock price date strings.
    E.g. "Mar 2024" -> "2024-03-01", "Dec 2012" -> "2012-12-01".
    """
    if not year_str:
        return None
    months = {
        "JAN": "01",
        "FEB": "02",
        "MAR": "03",
        "APR": "04",
        "MAY": "05",
        "JUN": "06",
        "JUL": "07",
        "AUG": "08",
        "SEP": "09",
        "OCT": "10",
        "NOV": "11",
        "DEC": "12",
    }
    match = re.search(r"\b([A-Za-z]{3})\s+(\d{4})\b", str(year_str).strip())
    if match:
        m = match.group(1).upper()
        y = match.group(2)
        m_num = months.get(m)
        if m_num:
            return f"{y}-{m_num}-01"
    return None
