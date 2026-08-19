"""
Report utilities for validation, sector mapping, data eligibility checks, and logging.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("report_utils")


def map_sector(broad_sector: str | None, sub_sector: str | None) -> str:
    """
    Maps database sector fields to the 11 standardized sectors:
    1. Communication Services
    2. Consumer Discretionary
    3. Consumer Staples
    4. Energy
    5. Banking
    6. Healthcare
    7. Industrials
    8. IT Services
    9. Materials
    10. Real Estate
    11. Utilities
    """
    broad_upper = str(broad_sector).strip().upper() if broad_sector else ""
    sub_upper = str(sub_sector).strip().upper() if sub_sector else ""

    if "INFORMATION TECHNOLOGY" in broad_upper:
        return "IT Services"
    elif "FINANCIALS" in broad_upper:
        return "Banking"
    elif "HEALTHCARE" in broad_upper:
        return "Healthcare"
    elif "ENERGY" in broad_upper and any(
        kw in sub_upper for kw in ["POWER", "UTILITIES", "TRANSMISSION", "RENEWABLE"]
    ):
        return "Utilities"
    else:
        return str(broad_sector).strip() if broad_sector else "Unclassified"


def check_eligibility(company_id: str, db_path: Path) -> tuple[bool, str]:
    """
    Verifies if a company has at least 3 years of financial records across:
    - financial_ratios
    - balancesheet
    - cashflow
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT COUNT(*) FROM financial_ratios WHERE company_id = ?",
            (company_id.upper(),),
        )
        ratio_cnt = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM balancesheet WHERE company_id = ?",
            (company_id.upper(),),
        )
        bs_cnt = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM cashflow WHERE company_id = ?",
            (company_id.upper(),),
        )
        cf_cnt = cursor.fetchone()[0]

        if ratio_cnt < 3 or bs_cnt < 3 or cf_cnt < 3:
            reasons = []
            if ratio_cnt < 3:
                reasons.append(f"financial_ratios ({ratio_cnt} yrs)")
            if bs_cnt < 3:
                reasons.append(f"balancesheet ({bs_cnt} yrs)")
            if cf_cnt < 3:
                reasons.append(f"cashflow ({cf_cnt} yrs)")
            return (
                False,
                f"Less than 3 years of financial data: {', '.join(reasons)}",
            )

        return True, ""
    except Exception as e:
        logger.error(f"Error checking eligibility for {company_id}: {e}")
        return False, f"Database error during eligibility check: {e}"
    finally:
        conn.close()


def validate_pdf(
    file_path: Path,
    expected_pages: int | None = None,
    min_size_kb: float = 30.0,
) -> tuple[bool, str]:
    """
    Validates a generated PDF:
    - File exists
    - File size is > min_size_kb
    - Page count matches expected_pages (if provided)
    """
    if not file_path.exists():
        return False, "File does not exist."

    size_bytes = file_path.stat().st_size
    size_kb = size_bytes / 1024.0

    if size_kb < min_size_kb:
        return (
            False,
            f"File size too small ({size_kb:.2f} KB, expected > {min_size_kb:.1f} KB)",
        )

    try:
        with open(file_path, "rb") as f:
            content = f.read()

        pages_raw = content.count(b"/Type /Page")
        parent_nodes = content.count(b"/Type /Pages")
        page_count = pages_raw - parent_nodes
        if page_count == 0:
            page_count = content.count(b"/Type/Page") - content.count(b"/Type/Pages")

        if expected_pages is not None and page_count != expected_pages:
            return (
                False,
                f"Page budget violation: got {page_count} pages, expected {expected_pages}",
            )

        return True, f"Valid (Size: {size_kb:.2f} KB, Pages: {page_count})"
    except Exception as e:
        logger.error(f"Error validating PDF {file_path.name}: {e}")
        return False, f"Binary parsing error: {e}"


def save_summary_reports(
    summary_data: list[dict[str, Any]],
    skipped_data: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    """
    Saves batch generation run summaries and skipped logs to CSV format.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save Batch Summary CSV
    if summary_data:
        df_sum = pd.DataFrame(summary_data)
        cols = [
            "Company ID",
            "Company Name",
            "Sector",
            "Status",
            "Page Count",
            "File Size (KB)",
            "Generation Time (s)",
        ]
        for col in cols:
            if col not in df_sum.columns:
                df_sum[col] = None
        df_sum = df_sum[cols]
        df_sum.to_csv(output_dir / "report_generation_summary.csv", index=False)
        logger.info(f"Saved run summary to {output_dir}/report_generation_summary.csv")

    # 2. Save Skipped Tearsheets CSV
    df_skip = pd.DataFrame(skipped_data)
    cols_skip = ["Company ID", "Company Name", "Sector", "Reason"]
    for col in cols_skip:
        if col not in df_skip.columns:
            df_skip[col] = None
    df_skip = df_skip[cols_skip]
    df_skip.to_csv(output_dir / "skipped_tearsheets.csv", index=False)
    logger.info(f"Saved skipped list to {output_dir}/skipped_tearsheets.csv")
