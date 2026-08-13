import sqlite3
from typing import Any, Dict, List
import pandas as pd
from src.config.settings import DB_PATH
from src.database.database import get_connection


def get_db_connection() -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.
    Explicitly enables row_factory and foreign keys.
    """
    conn = get_connection(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def clean_dict_nans(d: Dict[str, Any]) -> Dict[str, Any]:
    """Replaces any NaN values in a dictionary with None (JSON null)."""
    return {k: (None if pd.isna(v) else v) for k, v in d.items()}


def clean_df_nans(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Replaces any NaN values in a DataFrame with None and returns record dictionaries."""
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    return [clean_dict_nans(r) for r in records]
