"""
Financial Intelligence Engine — Automatic Pros & Cons Generator.
Evaluates 12 Pro and 12 Con rules for all companies, applies confidence scoring,
ensures full coverage, and exports the results to output/pros_cons_generated.csv.
"""

import logging
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import settings
from src.nlp.confidence import MIN_CONFIDENCE_THRESHOLD, score_sector_adjustment
from src.nlp.rules import RULES_REGISTRY
from src.utils.helpers import extract_year_int
from src.utils.logger import get_logger

# Setup logger for Pros/Cons generator
logger = get_logger("pros_cons")


def setup_generator_logging() -> logging.Logger:
    """Configures dedicated logging for the generator module to logs/pros_cons.log."""
    log_dir = settings.BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pros_cons.log"

    # Check if handler already exists to avoid duplicate logs
    pc_logger = logging.getLogger("pros_cons")
    for handler in list(pc_logger.handlers):
        pc_logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    pc_logger.addHandler(file_handler)
    pc_logger.setLevel(logging.INFO)
    return pc_logger


def load_generator_data(
    db_path: Path | None = None,
    raw_dir: Path | None = None,
    out_dir: Path | None = None,
) -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    """
    Loads and validates all required datasets from SQLite DB and output CSV files.
    """
    db_file = db_path or settings.DB_PATH
    raw_path = raw_dir or settings.RAW_DATA_DIR
    out_path = out_dir or (settings.BASE_DIR / "output")

    if not db_file.exists():
        logger.error(f"Database file not found: {db_file}")
        raise FileNotFoundError(f"Database file not found: {db_file}")

    conn = sqlite3.connect(str(db_file))

    try:
        # 1. Load companies
        df_companies = pd.read_sql_query(
            "SELECT id AS company_id, company_name FROM companies", conn
        )

        # 2. Load sectors
        df_sectors = pd.read_sql_query(
            "SELECT company_id, broad_sector AS sector FROM sectors", conn
        )

        # 3. Load financial_ratios, profitandloss, and balancesheet combined historical data
        query = """
            SELECT 
                fr.company_id,
                fr.year,
                fr.return_on_equity_pct,
                fr.return_on_capital_employed_pct,
                fr.debt_to_equity,
                fr.interest_coverage,
                fr.free_cash_flow_cr,
                fr.dividend_payout_ratio_pct,
                fr.revenue_cagr_5yr,
                fr.pat_cagr_5yr,
                fr.eps_cagr_5yr,
                pl.sales,
                pl.net_profit,
                pl.eps AS earnings_per_share,
                bs.total_assets,
                bs.borrowings
            FROM financial_ratios fr
            LEFT JOIN profitandloss pl ON fr.company_id = pl.company_id AND fr.year = pl.year
            LEFT JOIN balancesheet bs ON fr.company_id = bs.company_id AND fr.year = bs.year
        """
        df_financials = pd.read_sql_query(query, conn)

    finally:
        conn.close()

    # 4. Load cashflow_summary (for fcf_conversion)
    cf_summary_file = out_path / "cashflow_summary.csv"
    if cf_summary_file.exists():
        df_cf = pd.read_csv(cf_summary_file)
    else:
        logger.warning(
            f"cashflow_summary.csv not found at {cf_summary_file.resolve()}. Using empty template."
        )
        df_cf = pd.DataFrame(columns=["company_id", "year", "fcf_conversion"])

    # 5. Load analysis_parsed.csv (for validation step)
    analysis_parsed_file = out_path / "analysis_parsed.csv"
    if analysis_parsed_file.exists():
        df_analysis = pd.read_csv(analysis_parsed_file)
    else:
        logger.warning("analysis_parsed.csv not found. Using empty template.")
        df_analysis = pd.DataFrame(
            columns=["company_id", "metric_type", "period_years", "value_pct"]
        )

    # 6. Load capital_allocation.csv (for validation step)
    cap_alloc_file = out_path / "capital_allocation.csv"
    if cap_alloc_file.exists():
        pd.read_csv(cap_alloc_file)
    else:
        logger.warning("capital_allocation.csv not found. Using empty template.")
        pd.DataFrame(columns=["company_id", "year", "pattern_label"])

    # 7. Load dividend yield from market_cap.xlsx
    mcap_file = raw_path / "market_cap.xlsx"
    if mcap_file.exists():
        df_mcap = pd.read_excel(mcap_file)
    else:
        logger.warning(
            f"market_cap.xlsx not found at {mcap_file}. Using empty template."
        )
        df_mcap = pd.DataFrame(columns=["company_id", "year", "dividend_yield_pct"])

    # Perform input validations
    if df_companies.empty:
        raise ValueError("Companies table is empty.")
    if df_financials.empty:
        raise ValueError("Financials data is empty.")

    logger.info("Successfully loaded all required datasets for Pros & Cons evaluation.")
    return (
        df_companies,
        df_sectors,
        df_financials,
        df_cf,
        df_div_yield(df_mcap),
        df_analysis,
    )


def df_div_yield(df_mcap: pd.DataFrame) -> pd.DataFrame:
    """Helper to extract latest dividend yield per company from market cap data."""
    if df_mcap.empty or "dividend_yield_pct" not in df_mcap.columns:
        return pd.DataFrame(columns=["company_id", "dividend_yield_pct"])

    df = df_mcap.copy()
    df["company_id"] = df["company_id"].astype(str).str.strip().str.upper()
    df["year_int"] = df["year"].apply(extract_year_int)

    # Sort chronologically and keep the latest year's record
    df_sorted = df.dropna(subset=["year_int"]).sort_values(by="year_int")
    df_latest = df_sorted.drop_duplicates(subset=["company_id"], keep="last")

    return df_latest[["company_id", "dividend_yield_pct"]]


def compile_company_histories(
    df_financials: pd.DataFrame, df_cf: pd.DataFrame, df_div: pd.DataFrame
) -> dict[str, list[dict[str, Any]]]:
    """
    Compiles database and CSV metrics into a dictionary mapping company_id -> list of annual records.
    Records are sorted chronologically by year integer.
    """
    df_fin = df_financials.copy()
    df_fin["company_id"] = df_fin["company_id"].astype(str).str.strip().str.upper()
    df_fin["year_int"] = df_fin["year"].apply(extract_year_int)
    df_fin = df_fin.dropna(subset=["year_int"])
    df_fin["year_int"] = df_fin["year_int"].astype(int)

    # Parse cashflow summary years
    df_cflow = df_cf.copy()
    if not df_cflow.empty and "company_id" in df_cflow.columns:
        df_cflow["company_id"] = (
            df_cflow["company_id"].astype(str).str.strip().str.upper()
        )
        df_cflow["year_int"] = df_cflow["year"].apply(extract_year_int)
        df_cflow = df_cflow.dropna(subset=["year_int"])
        df_cflow["year_int"] = df_cflow["year_int"].astype(int)

        # Merge financials and cashflow on company and year
        df_merged = pd.merge(
            df_fin,
            df_cflow[["company_id", "year_int", "fcf_conversion"]],
            on=["company_id", "year_int"],
            how="left",
        )
    else:
        df_merged = df_fin.copy()
        df_merged["fcf_conversion"] = None

    # Merge latest dividend yield
    if not df_div.empty:
        df_merged = pd.merge(df_merged, df_div, on="company_id", how="left")
    else:
        df_merged["dividend_yield_pct"] = None

    # Group by company_id and build histories
    histories: dict[str, list[dict[str, Any]]] = {}
    for cid, group in df_merged.groupby("company_id"):
        # Sort chronologically by year_int ascending
        group_sorted = group.sort_values(by="year_int")
        histories[cid] = group_sorted.to_dict(orient="records")

    return histories


def run_pros_cons_pipeline():
    """Executes the automatic Pros & Cons generation engine."""
    start_time = time.time()
    pc_log = setup_generator_logging()
    pc_log.info("Starting automatic Pros & Cons Generation Engine...")

    out_dir = settings.BASE_DIR / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load required datasets
        df_companies, df_sectors, df_financials, df_cf, df_div, _df_analysis = (
            load_generator_data()
        )

        # Sector mapping
        sectors_map = dict(
            zip(df_sectors["company_id"].str.strip().str.upper(), df_sectors["sector"])
        )

        # Compile company history records
        company_histories = compile_company_histories(df_financials, df_cf, df_div)

    except Exception as e:
        pc_log.critical(f"Data loading failed: {e}", exc_info=True)
        print(
            f"CRITICAL: Pros/Cons Generator failed to load data: {e}", file=sys.stderr
        )
        return

    generated_records = []
    total_rules_triggered = 0
    total_confidence_sum = 0.0
    companies_processed_count = 0

    # Process each company in the database master
    for idx, row in df_companies.iterrows():
        company_id = str(row["company_id"]).strip().upper()
        companies_processed_count += 1

        sector = sectors_map.get(company_id, "Other")
        history = company_histories.get(company_id, [])

        pros_count = 0
        cons_count = 0

        # Evaluate all rules from the registry
        for rule in RULES_REGISTRY:
            result = rule.evaluate(history, sector)
            if result:
                # Apply sector adjustments to confidence score
                adjusted_score = score_sector_adjustment(
                    result["confidence_pct"], rule.rule_id, sector
                )
                result["confidence_pct"] = adjusted_score

                # Filter by minimum confidence threshold
                if adjusted_score >= MIN_CONFIDENCE_THRESHOLD:
                    generated_records.append(
                        {
                            "company_id": company_id,
                            "type": result["type"],
                            "rule_id": result["rule_id"],
                            "text": result["text"],
                            "confidence_pct": result["confidence_pct"],
                        }
                    )
                    total_rules_triggered += 1
                    total_confidence_sum += adjusted_score

                    if result["type"] == "PRO":
                        pros_count += 1
                    else:
                        cons_count += 1

        # Step 9: Guarantee Coverage - fallback insights if none triggered
        if pros_count == 0:
            generated_records.append(
                {
                    "company_id": company_id,
                    "type": "PRO",
                    "rule_id": "PRO-FALLBACK",
                    "text": "No significant positive signals detected.",
                    "confidence_pct": 60.0,
                }
            )
            total_rules_triggered += 1
            total_confidence_sum += 60.0
            pc_log.info(f"[{company_id}] Generated fallback PRO insight.")

        if cons_count == 0:
            generated_records.append(
                {
                    "company_id": company_id,
                    "type": "CON",
                    "rule_id": "CON-FALLBACK",
                    "text": "No major financial concerns identified.",
                    "confidence_pct": 60.0,
                }
            )
            total_rules_triggered += 1
            total_confidence_sum += 60.0
            pc_log.info(f"[{company_id}] Generated fallback CON insight.")

    # Build output DataFrame
    df_out = pd.DataFrame(generated_records)

    # Sort output: Company -> Type (PRO before CON) -> Confidence (DESC)
    # Since we want PRO (starts with P) before CON (starts with C), we sort Type descending
    df_out = df_out.sort_values(
        by=["company_id", "type", "confidence_pct"], ascending=[True, False, False]
    ).reset_index(drop=True)

    # Export to CSV
    out_csv_path = out_dir / "pros_cons_generated.csv"
    df_out.to_csv(out_csv_path, index=False)

    avg_confidence = (
        round(total_confidence_sum / total_rules_triggered, 2)
        if total_rules_triggered > 0
        else 0.0
    )
    runtime = round(time.time() - start_time, 4)

    # Log execution stats
    pc_log.info(
        f"Pros/Cons Engine finished in {runtime}s. "
        f"Companies Processed: {companies_processed_count}, "
        f"Insights Exported: {len(df_out)} rows, "
        f"Average Confidence: {avg_confidence}%."
    )

    # Perform Validation checks (Step 13)
    validation_passed = True
    val_msg = []

    # 1. 92 companies processed check
    if companies_processed_count != 92:
        val_msg.append(
            f"Validation Warning: Processed {companies_processed_count} companies (expected 92)."
        )
        validation_passed = False

    # 2. At least 1 Pro and 1 Con per company check
    for cid in df_companies["company_id"].unique():
        cid_upper = str(cid).strip().upper()
        comp_records = df_out[df_out["company_id"] == cid_upper]
        p_c = comp_records[comp_records["type"] == "PRO"]
        c_c = comp_records[comp_records["type"] == "CON"]
        if p_c.empty:
            val_msg.append(f"Validation Fail: {cid_upper} has no PRO insights.")
            validation_passed = False
        if c_c.empty:
            val_msg.append(f"Validation Fail: {cid_upper} has no CON insights.")
            validation_passed = False

    # 3. Confidence range check
    if not df_out.empty:
        min_conf = df_out["confidence_pct"].min()
        max_conf = df_out["confidence_pct"].max()
        if min_conf < 0.0 or max_conf > 100.0:
            val_msg.append(
                f"Validation Fail: Confidence scores out of bounds [{min_conf}, {max_conf}]."
            )
            validation_passed = False

    # 4. Duplicate rule IDs check (Ensure no duplicate rule_id in registry)
    registered_ids = [r.rule_id for r in RULES_REGISTRY]
    if len(registered_ids) != len(set(registered_ids)):
        val_msg.append(
            f"Validation Fail: Duplicate rule IDs detected in registry: {registered_ids}"
        )
        validation_passed = False

    if validation_passed:
        pc_log.info(
            "Validation passed successfully! Coverage: 100%. no duplicate rules, confidence within [0, 100]."
        )
    else:
        pc_log.error(f"Validation failed with errors: {val_msg}")

    print("=" * 80)
    print("             FINANCIAL INTELLIGENCE PROS & CONS GENERATOR             ")
    print("=" * 80)
    print(f"[+] Total Companies Processed : {companies_processed_count}")
    print(f"    Insights Generated        : {len(df_out)}")
    print(f"    Average Confidence Score  : {avg_confidence}%")
    print(f"    Engine Runtime            : {runtime}s")
    print(f"    Output CSV File Path      : {out_csv_path}")
    print(
        f"    Validation Status         : {'PASSED' if validation_passed else 'FAILED'}"
    )
    if not validation_passed:
        for m in val_msg:
            print(f"    [!] {m}", file=sys.stderr)
    print("-" * 80)


if __name__ == "__main__":
    run_pros_cons_pipeline()
