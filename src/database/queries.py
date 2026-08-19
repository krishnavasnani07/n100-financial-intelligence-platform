from pathlib import Path
from typing import Any

import pandas as pd

from src.database.database import get_db
from src.utils.logger import get_logger

logger = get_logger(__name__)


def get_table_counts(db_path: Path | str | None = None) -> dict[str, int]:
    """
    Returns a dictionary mapping table names to row counts.
    """
    counts = {}
    query_tables = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%';
    """
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query_tables)
        tables = [row[0] for row in cursor.fetchall()]

        for table in sorted(tables):
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            counts[table] = cursor.fetchone()[0]

    return counts


def check_foreign_key_violations(
    db_path: Path | str | None = None,
) -> list[tuple]:
    """
    Runs 'PRAGMA foreign_key_check;' and returns any constraint violation records.
    Expected output for valid DB load: empty list (0 rows).
    """
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_key_check;")
        violations = cursor.fetchall()

    if violations:
        logger.warning(
            f"Found {len(violations)} foreign key violations in the database."
        )
    else:
        logger.info("Foreign key check passed cleanly. 0 violations found.")

    return violations


def query_to_dataframe(
    sql: str,
    db_path: Path | str | None = None,
    params: list | dict | tuple | Any | None = None,
) -> pd.DataFrame:
    """
    Executes a SELECT query and returns the result as a pandas DataFrame.
    """
    with get_db(db_path) as conn:
        df = pd.read_sql_query(sql, conn, params=params)
    return df
