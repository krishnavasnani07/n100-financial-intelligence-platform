from pathlib import Path
import re
from typing import List, Any, Optional
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
