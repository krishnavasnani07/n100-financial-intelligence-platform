from pathlib import Path
from typing import List
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
