"""
Batch PDF Report Generator.
Orchestrates tearsheet compilation for all eligible companies, runs layout validations,
and exports run reports.
"""

from __future__ import annotations

import argparse
import sqlite3
import time
from pathlib import Path

from src.config.settings import DB_PATH, OUTPUT_DIR
from src.reports.report_utils import (
    check_eligibility,
    map_sector,
    save_summary_reports,
    validate_pdf,
)
from src.reports.tearsheet import generate_tearsheet
from src.utils.logger import get_logger

logger = get_logger("batch_generator")


def run_batch_generation(
    ticker_list: list[str] | None = None,
    db_path: Path | None = None,
    out_dir: Path | None = None,
) -> None:
    """
    Runs batch generation for the specified list of tickers (or all if None).
    """
    db_file = db_path or DB_PATH
    output_dir = out_dir or OUTPUT_DIR

    # 1. Fetch companies and sector information
    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        # Join companies with sectors to have sector information early
        cursor.execute("""
            SELECT c.id, c.company_name, s.broad_sector, s.sub_sector
            FROM companies c
            LEFT JOIN sectors s ON c.id = s.company_id
            """)
        all_companies = cursor.fetchall()
    except Exception as e:
        logger.error(f"Failed to fetch companies from database: {e}")
        return
    finally:
        conn.close()

    # 2. Filter cohort based on ticker_list if provided
    if ticker_list:
        ticker_set = {t.strip().upper() for t in ticker_list}
        cohort = [c for c in all_companies if c[0].upper() in ticker_set]
    else:
        cohort = all_companies

    logger.info(f"Loaded cohort of {len(cohort)} companies for batch run.")

    summary_data = []
    skipped_data = []

    for comp_id, comp_name, broad_sector, sub_sector in cohort:
        sector_name = map_sector(broad_sector, sub_sector)
        logger.info(f"--- Processing {comp_id} ({comp_name}) ---")

        # Check eligibility (min 3 years data in ratios, balance sheet, cash flow)
        eligible, reason = check_eligibility(comp_id, db_file)
        if not eligible:
            logger.warning(f"Company {comp_id} is skipped. Reason: {reason}")
            skipped_data.append(
                {
                    "Company ID": comp_id,
                    "Company Name": comp_name,
                    "Sector": sector_name,
                    "Reason": reason,
                }
            )
            summary_data.append(
                {
                    "Company ID": comp_id,
                    "Company Name": comp_name,
                    "Sector": sector_name,
                    "Status": "Skipped",
                    "Page Count": 0,
                    "File Size (KB)": 0.0,
                    "Generation Time (s)": 0.0,
                }
            )
            continue

        # Try generating tearsheet
        start_time = time.time()
        try:
            pdf_path = generate_tearsheet(comp_id, db_file)
            gen_time = round(time.time() - start_time, 2)

            # Post-generation layout & size validations
            valid, val_msg = validate_pdf(pdf_path, expected_pages=2)
            size_kb = (
                round(pdf_path.stat().st_size / 1024.0, 2) if pdf_path.exists() else 0.0
            )

            if valid:
                logger.info(f"Company {comp_id} Tearsheet validated: {val_msg}")
                summary_data.append(
                    {
                        "Company ID": comp_id,
                        "Company Name": comp_name,
                        "Sector": sector_name,
                        "Status": "Generated",
                        "Page Count": 2,
                        "File Size (KB)": size_kb,
                        "Generation Time (s)": gen_time,
                    }
                )
            else:
                logger.error(
                    f"Company {comp_id} Tearsheet validation failed: {val_msg}"
                )
                summary_data.append(
                    {
                        "Company ID": comp_id,
                        "Company Name": comp_name,
                        "Sector": sector_name,
                        "Status": f"Failed ({val_msg})",
                        "Page Count": 0,
                        "File Size (KB)": size_kb,
                        "Generation Time (s)": gen_time,
                    }
                )
                skipped_data.append(
                    {
                        "Company ID": comp_id,
                        "Company Name": comp_name,
                        "Sector": sector_name,
                        "Reason": f"Validation failure: {val_msg}",
                    }
                )
        except Exception as e:
            gen_time = round(time.time() - start_time, 2)
            logger.error(
                f"Error generating tearsheet for {comp_id}: {e}", exc_info=True
            )
            summary_data.append(
                {
                    "Company ID": comp_id,
                    "Company Name": comp_name,
                    "Sector": sector_name,
                    "Status": "Failed (Error)",
                    "Page Count": 0,
                    "File Size (KB)": 0.0,
                    "Generation Time (s)": gen_time,
                }
            )
            skipped_data.append(
                {
                    "Company ID": comp_id,
                    "Company Name": comp_name,
                    "Sector": sector_name,
                    "Reason": f"Generation error: {e}",
                }
            )

    # Save summary files
    save_summary_reports(summary_data, skipped_data, output_dir)
    logger.info("Batch report generation completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Batch Tearsheet Generator")
    parser.add_argument(
        "--tickers",
        type=str,
        help="Comma-separated list of NSE tickers to run. If not provided, runs all companies.",
    )
    parser.add_argument("--db", type=str, help="Custom database file path.")
    parser.add_argument("--output", type=str, help="Custom output summary directory.")
    args = parser.parse_args()

    tickers = args.tickers.split(",") if args.tickers else None
    db = Path(args.db) if args.db else None
    output = Path(args.output) if args.output else None

    run_batch_generation(ticker_list=tickers, db_path=db, out_dir=output)
