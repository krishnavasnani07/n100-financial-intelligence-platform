"""
NLP Analysis Text Parser & Structured Data Extraction Engine.
Extracts CAGR and financial growth metrics from unstructured text fields in analysis.xlsx,
performs cross-validation against ratio engine outputs, and generates validation reports.
"""

import logging
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.config import settings
from src.utils.helpers import extract_year_int
from src.utils.logger import get_logger

# Setup logger for NLP parser
logger = get_logger("nlp_parser")


def setup_parser_logging() -> logging.Logger:
    """Configures dedicated logging for the parser module to logs/parser.log."""
    log_dir = settings.BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "parser.log"

    # Check if file handler already exists to avoid duplicate logs
    parser_logger = logging.getLogger("nlp_parser")
    for handler in list(parser_logger.handlers):
        parser_logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    parser_logger.addHandler(file_handler)
    parser_logger.setLevel(logging.INFO)
    return parser_logger


# Core mappings of raw Excel columns to standardized metric types
METRIC_MAPPING = {
    "compounded_sales_growth": "Sales CAGR",
    "compounded_profit_growth": "Profit CAGR",
    "stock_price_cagr": "Stock Price CAGR",
    "roe": "ROE",
}


def load_analysis_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Loads and validates raw analysis sheet from analysis.xlsx."""
    file_path = Path(filepath) if filepath else settings.RAW_DATA_DIR / "analysis.xlsx"
    if not file_path.exists():
        logger.error(f"Analysis file not found: {file_path.resolve()}")
        raise FileNotFoundError(f"Missing analysis file: {file_path}")

    # Read Excel, skipping title block row
    df = pd.read_excel(file_path, skiprows=1)

    # Required columns check
    required_cols = [
        "company_id",
        "compounded_sales_growth",
        "compounded_profit_growth",
        "stock_price_cagr",
        "roe",
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in analysis sheet: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info(f"Successfully loaded raw analysis sheet with {len(df)} records.")
    return df


def load_companies(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Loads companies sheet to validate tickers."""
    file_path = Path(filepath) if filepath else settings.RAW_DATA_DIR / "companies.xlsx"
    if not file_path.exists():
        logger.error(f"Companies file not found: {file_path.resolve()}")
        raise FileNotFoundError(f"Missing companies file: {file_path}")

    df = pd.read_excel(file_path, skiprows=1)
    if "id" not in df.columns:
        logger.error("Missing company ID column in companies sheet.")
        raise ValueError("Missing 'id' column in companies sheet.")

    # Check duplicate company IDs
    dup_ids = df[df.duplicated(subset=["id"], keep=False)]["id"].unique()
    if len(dup_ids) > 0:
        logger.warning(
            f"Duplicate company IDs detected in companies sheet: {list(dup_ids)}"
        )

    return df


def load_ratio_engine_output(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Establishes database connection to retrieve computed ratio outputs."""
    db_file = Path(db_path) if db_path else settings.DB_PATH
    if not db_file.exists():
        logger.error(f"Database file not found at {db_file.resolve()}")
        raise FileNotFoundError(f"Database file not found: {db_file}")
    conn = sqlite3.connect(str(db_file))
    return conn


def load_growth_engine_output(
    filepath: Optional[Path] = None,
) -> Optional[pd.DataFrame]:
    """Loads precomputed growth engine summaries from output/growth_summary.csv."""
    file_path = (
        Path(filepath)
        if filepath
        else settings.BASE_DIR / "output" / "growth_summary.csv"
    )
    if not file_path.exists():
        logger.warning(
            f"Growth summary file not found at {file_path.resolve()}. Skipping load."
        )
        return None
    df = pd.read_csv(file_path)
    return df


def parse_growth_metric(text: Any, metric_type: str) -> Optional[List[Dict[str, Any]]]:
    """
    Parses a growth metric text string using the regex.
    Extracts period (years) and CAGR value (percentage).
    Supports multiple entries in a single string (separated by newlines or commas).
    """
    if pd.isna(text) or not str(text).strip():
        return None

    text_str = str(text).strip()

    # Regular expression supporting positive, decimal, and negative CAGR values
    pattern = r"(\d+)\s*Years?\s*:?\s*(-?[\d.]+)%"

    matches = re.findall(pattern, text_str)
    if not matches:
        return None

    parsed_results = []
    for match in matches:
        period = int(match[0])
        val = float(match[1])
        parsed_results.append(
            {"metric_type": metric_type, "period_years": period, "value_pct": val}
        )

    return parsed_results


def get_computed_value(
    company_id: str,
    metric_type: str,
    period_years: int,
    db_conn: sqlite3.Connection,
    growth_df: Optional[pd.DataFrame],
) -> Optional[float]:
    """Retrieves computed CAGR/ROE values from Ratio Engine results for comparison."""
    if metric_type == "Sales CAGR":
        col = f"Revenue_{period_years}Y"
        if growth_df is not None and col in growth_df.columns:
            val_series = growth_df.loc[growth_df["Company"] == company_id, col].values
            if len(val_series) > 0 and not pd.isna(val_series[0]):
                return float(val_series[0])

    elif metric_type == "Profit CAGR":
        col = f"PAT_{period_years}Y"
        if growth_df is not None and col in growth_df.columns:
            val_series = growth_df.loc[growth_df["Company"] == company_id, col].values
            if len(val_series) > 0 and not pd.isna(val_series[0]):
                return float(val_series[0])

    elif metric_type == "ROE":
        # Look up ROE values in financial_ratios table
        cur = db_conn.cursor()
        cur.execute(
            "SELECT return_on_equity_pct, year FROM financial_ratios WHERE company_id = ?",
            (company_id,),
        )
        rows = cur.fetchall()
        if not rows:
            return None

        # Parse years to integers and sort DESC
        parsed_rows = []
        for roe_val, yr_val in rows:
            yr_int = extract_year_int(yr_val)
            if yr_int is not None and roe_val is not None:
                parsed_rows.append((roe_val, yr_int))

        parsed_rows.sort(key=lambda x: x[1], reverse=True)
        if not parsed_rows:
            return None

        # Period = 1 means "Last Year" / "1 Year" / latest record
        if period_years == 1:
            return float(parsed_rows[0][0])

        # Otherwise, average ROE over the last N years
        target_vals = [r[0] for r in parsed_rows[:period_years]]
        if target_vals:
            return float(sum(target_vals) / len(target_vals))

    return None


def run_nlp_pipeline():
    """Main orchestrator executing the NLP text parser and CAGR validation pipeline."""
    import time

    start_time = time.time()

    # Configure logs
    parser_log = setup_parser_logging()
    parser_log.info("Starting NLP Ingestion & Structured Data Parsing Engine...")

    # Create output dir
    output_dir = settings.BASE_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load datasets
        df_analysis = load_analysis_data()
        df_companies = load_companies()
        valid_tickers = set(
            df_companies["id"].dropna().astype(str).str.strip().unique()
        )

        db_conn = load_ratio_engine_output()
        df_growth = load_growth_engine_output()

    except Exception as e:
        parser_log.critical(f"Pipeline initialization failed: {e}", exc_info=True)
        print(f"CRITICAL: NLP Pipeline initialization failed: {e}", file=sys.stderr)
        return

    parsed_records = []
    failures = []

    total_companies_processed = 0
    successful_parses_count = 0
    failed_parses_count = 0

    # Process each row
    for idx, row in df_analysis.iterrows():
        company_id = str(row["company_id"]).strip()
        total_companies_processed += 1

        # Verify foreign key mapping to companies list
        if company_id not in valid_tickers:
            parser_log.warning(
                f"Company ID '{company_id}' not found in companies list. Skipping."
            )
            continue

        for col_name, metric_type in METRIC_MAPPING.items():
            cell_text = row[col_name]

            # Check missing analysis text
            if pd.isna(cell_text) or not str(cell_text).strip():
                failures.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric_type,
                        "original_text": "",
                        "failure_reason": "Empty text",
                    }
                )
                failed_parses_count += 1
                parser_log.warning(
                    f"[{company_id}] {metric_type} parsing failed: Empty text."
                )
                continue

            parsed_matches = parse_growth_metric(cell_text, metric_type)
            if not parsed_matches:
                # Parsing failed
                failures.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric_type,
                        "original_text": str(cell_text).strip(),
                        "failure_reason": (
                            "Invalid format"
                            if "Year" in str(cell_text) or "%" in str(cell_text)
                            else "Unexpected wording"
                        ),
                    }
                )
                failed_parses_count += 1
                parser_log.warning(
                    f"[{company_id}] {metric_type} parsing failed: Invalid format/wording for '{cell_text}'."
                )
            else:
                # Parsed successfully
                for match in parsed_matches:
                    parsed_records.append(
                        {
                            "company_id": company_id,
                            "metric_type": match["metric_type"],
                            "period_years": match["period_years"],
                            "value_pct": match["value_pct"],
                        }
                    )
                    successful_parses_count += 1
                    parser_log.debug(
                        f"[{company_id}] {metric_type} parsed: {match['period_years']}Y -> {match['value_pct']}%"
                    )

    # Generate structured dataset: analysis_parsed.csv
    df_parsed = pd.DataFrame(parsed_records)
    if not df_parsed.empty:
        # Sort by company_id, metric_type, period_years
        df_parsed = df_parsed.sort_values(
            by=["company_id", "metric_type", "period_years"]
        )
        parsed_out_path = output_dir / "analysis_parsed.csv"
        df_parsed.to_csv(parsed_out_path, index=False)
        parser_log.info(
            f"Structured dataset written to {parsed_out_path.resolve()} with {len(df_parsed)} rows."
        )
    else:
        parser_log.warning(
            "No successfully parsed records. analysis_parsed.csv not written."
        )

    # Generate parse failures dataset: parse_failures.csv
    df_failures = pd.DataFrame(failures)
    failures_out_path = output_dir / "parse_failures.csv"
    df_failures.to_csv(failures_out_path, index=False)
    parser_log.info(
        f"Parse failures report written to {failures_out_path.resolve()} with {len(df_failures)} rows."
    )

    # Perform cross-validation and generate report
    validation_records = []
    validation_mismatches_count = 0

    if not df_parsed.empty:
        for idx, row in df_parsed.iterrows():
            company_id = row["company_id"]
            metric_type = row["metric_type"]
            period_years = row["period_years"]
            parsed_val = row["value_pct"]

            # Map ROE terms like "1 year" or "Last Year"
            # Note: parse_growth_metric handles digits, so "Last Year" or "TTM" are already logged in parse_failures.csv.
            # Only numeric periods (e.g. 10, 5, 3, 1) are parsed and validated.
            computed_val = get_computed_value(
                company_id, metric_type, period_years, db_conn, df_growth
            )

            if computed_val is None:
                # If no computed value is available in calculations (e.g., Stock Price CAGR or Zero-Base), mark as review needed
                diff_pct = None
                review_required = "REVIEW"
                validation_mismatches_count += 1
                parser_log.info(
                    f"[{company_id}] {metric_type} {period_years}Y: No computed value found for comparison. Flagged for review."
                )
            else:
                # Compute absolute difference
                diff_pct = round(abs(parsed_val - computed_val), 4)

                # Rule: > 5% absolute difference triggers a REVIEW flag
                if diff_pct > 5.0:
                    review_required = "REVIEW"
                    validation_mismatches_count += 1
                    parser_log.warning(
                        f"[{company_id}] {metric_type} {period_years}Y: Mismatch detected! "
                        f"Parsed={parsed_val}%, Computed={computed_val}%, Diff={diff_pct}%"
                    )
                else:
                    review_required = "PASS"

            validation_records.append(
                {
                    "company_id": company_id,
                    "metric_type": f"{metric_type} {period_years}Y",
                    "parsed_value": parsed_val,
                    "computed_value": (
                        computed_val if computed_val is not None else np.nan
                    ),
                    "difference_pct": diff_pct if diff_pct is not None else np.nan,
                    "review_required": review_required,
                }
            )

    df_val = pd.DataFrame(validation_records)
    val_out_path = output_dir / "cagr_validation_report.csv"
    df_val.to_csv(val_out_path, index=False)
    parser_log.info(
        f"CAGR validation report written to {val_out_path.resolve()} with {len(df_val)} rows."
    )

    # Close connection
    db_conn.close()

    runtime = round(time.time() - start_time, 4)
    parser_log.info(
        f"NLP Pipeline complete in {runtime}s. "
        f"Processed: {total_companies_processed} companies, "
        f"Parsed: {successful_parses_count} successes, {failed_parses_count} failures. "
        f"Validation: {validation_mismatches_count} review flags generated."
    )

    print("=" * 80)
    print("                 NLP TEXT PARSER & CAGR VALIDATION ENGINE                 ")
    print("=" * 80)
    print(f"[+] Total Companies Processed : {total_companies_processed}")
    print(f"    Successful Parses         : {successful_parses_count}")
    print(f"    Failed Parses (Logged)     : {failed_parses_count}")
    print(f"    Validation Mismatches     : {validation_mismatches_count}")
    print(f"    Pipeline Runtime          : {runtime}s")
    print(f"    Parsed Output Path        : {parsed_out_path}")
    print(f"    Failures Output Path      : {failures_out_path}")
    print(f"    Validation Report Path    : {val_out_path}")
    print("-" * 80)


if __name__ == "__main__":
    run_nlp_pipeline()
