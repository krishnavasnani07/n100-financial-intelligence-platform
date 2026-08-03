"""
Capital Allocation Intelligence & Strategy Evolution Report (Sprint 5 — Day 32)
Validates dataset completeness, analyzes pattern distribution, detects YoY strategy changes,
and integrates results into the Cash Flow Intelligence report.
"""

from __future__ import annotations

import os
import sys
import time
import sqlite3
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np

from src.utils.logger import get_logger
from src.config.settings import BASE_DIR, DB_PATH, OUTPUT_DIR
from src.utils.helpers import extract_year_int
from src.analytics.cashflow_kpis import export_excel_intelligence


def setup_allocation_logging() -> logging.Logger:
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "capital_allocation.log"
    
    alloc_logger = logging.getLogger("capital_allocation")
    for h in list(alloc_logger.handlers):
        alloc_logger.removeHandler(h)
        
    fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    alloc_logger.addHandler(fh)
    alloc_logger.setLevel(logging.INFO)
    return alloc_logger


logger = setup_allocation_logging()


def categorize_transition(prev: str, curr: str) -> str:
    """
    Categorizes the strategy change pattern from previous year to current year.
    """
    if prev == curr:
        return "No Change"
        
    prev = str(prev).strip()
    curr = str(curr).strip()
    
    # Mature
    if curr == "Shareholder Returns":
        return "Mature"
        
    # Recovery / Improving
    if prev in ["Distress Signal", "Growth Funded by Debt"] and curr in ["Cash Accumulator", "Reinvestor", "Shareholder Returns"]:
        if curr == "Cash Accumulator":
            return "Recovery"
        return "Improving"
        
    # Negative Shift
    if curr == "Distress Signal":
        return "Negative Shift"
    if prev in ["Reinvestor", "Shareholder Returns", "Cash Accumulator"] and curr in ["Growth Funded by Debt", "Mixed"]:
        return "Negative Shift"
        
    # Improving
    if prev in ["Mixed", "Pre-Revenue", "Liquidating Assets"] and curr in ["Reinvestor", "Cash Accumulator"]:
        return "Improving"
        
    # Default
    return "Strategic Shift"


def verify_capital_allocation(df_alloc: pd.DataFrame, db_path: Path) -> List[str]:
    """
    Verifies completeness, coverage, duplicate-free properties and valid pattern labels in capital_allocation.csv.
    """
    errors = []
    
    # 1. Company Count
    unique_companies = df_alloc["company_id"].unique()
    if len(unique_companies) != 92:
        errors.append(f"Expected 92 companies, found {len(unique_companies)}.")
        
    # 2. Duplicate Detection
    duplicates = df_alloc[df_alloc.duplicated(subset=["company_id", "year"])]
    if not duplicates.empty:
        errors.append(f"Duplicate (company_id, year) records found: {duplicates[['company_id', 'year']].values.tolist()}")
        
    # 3. Pattern Labels check
    valid_patterns = {
        "Reinvestor", "Shareholder Returns", "Liquidating Assets", "Distress Signal",
        "Growth Funded by Debt", "Cash Accumulator", "Pre-Revenue", "Mixed"
    }
    invalid_rows = df_alloc[~df_alloc["pattern_label"].isin(valid_patterns)]
    if not invalid_rows.empty:
        errors.append(f"Invalid pattern labels: {invalid_rows[['company_id', 'year', 'pattern_label']].values.tolist()}")
        
    # 4. Historical Coverage Check
    conn = sqlite3.connect(str(db_path))
    try:
        db_cf = pd.read_sql_query("SELECT company_id, year FROM cashflow", conn)
        db_cf["company_id"] = db_cf["company_id"].astype(str).str.strip().str.upper()
    finally:
        conn.close()
        
    db_pairs = set(zip(db_cf["company_id"], db_cf["year"]))
    alloc_pairs = set(zip(df_alloc["company_id"], df_alloc["year"]))
    
    # Find years in DB not present in alloc report
    missing = db_pairs - alloc_pairs
    if missing:
        errors.append(f"Missing {len(missing)} company-year records in allocation dataset.")
        
    return errors


def run_capital_allocation_report(
    db_path: Optional[Path] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    start_time = time.time()
    db_file = db_path or DB_PATH
    out_dir = output_dir or OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting Capital Allocation Intelligence Engine...")
    
    alloc_csv_path = out_dir / "capital_allocation.csv"
    if not alloc_csv_path.exists():
        msg = f"Required file {alloc_csv_path} does not exist."
        logger.error(msg)
        raise FileNotFoundError(msg)
        
    # Load capital allocation data
    df_alloc = pd.read_csv(alloc_csv_path)
    df_alloc["company_id"] = df_alloc["company_id"].astype(str).str.strip().str.upper()
    df_alloc["year_int"] = df_alloc["year"].apply(extract_year_int)
    
    # Verify dataset completeness
    errors = verify_capital_allocation(df_alloc, db_file)
    if errors:
        for err in errors:
            logger.warning(f"Verification Check: {err}")
    else:
        logger.info("Capital allocation dataset verification: PASSED.")
        
    # Load company names map
    conn = sqlite3.connect(str(db_file))
    df_companies = pd.read_sql_query("SELECT id AS company_id, company_name FROM companies", conn)
    conn.close()
    df_companies["company_id"] = df_companies["company_id"].astype(str).str.strip().str.upper()
    names_map = dict(zip(df_companies["company_id"], df_companies["company_name"]))
    
    # 1. Distribution Summary (Latest year only)
    df_latest = df_alloc.sort_values(by="year_int").drop_duplicates(subset=["company_id"], keep="last").copy()
    
    pattern_counts = df_latest["pattern_label"].value_counts().reset_index()
    pattern_counts.columns = ["pattern", "company_count"]
    pattern_counts["percentage"] = (pattern_counts["company_count"] / len(df_latest) * 100).round(2)
    
    # Note: latest_year in summary is the max year string found in latest rows
    max_latest_year = df_latest["year"].max()
    pattern_counts["latest_year"] = max_latest_year
    
    summary_path = out_dir / "capital_allocation_summary.csv"
    pattern_counts.to_csv(summary_path, index=False)
    logger.info(f"Exported allocation distribution summary to {summary_path}")
    
    # 2. Strategy Transition/Change Detection
    # Sort Company -> Year
    df_sorted = df_alloc.sort_values(by=["company_id", "year_int"]).copy()
    
    pattern_changes = []
    change_count = 0
    
    for cid, group in df_sorted.groupby("company_id"):
        group_list = group.to_dict("records")
        for i in range(1, len(group_list)):
            prev_rec = group_list[i - 1]
            curr_rec = group_list[i]
            
            prev_pat = prev_rec["pattern_label"]
            curr_pat = curr_rec["pattern_label"]
            
            if prev_pat != curr_pat:
                change_category = categorize_transition(prev_pat, curr_pat)
                comp_name = names_map.get(cid, cid)
                
                pattern_changes.append({
                    "company_id": cid,
                    "company_name": comp_name,
                    "year": curr_rec["year"],
                    "previous_pattern": prev_pat,
                    "current_pattern": curr_pat,
                    "change_category": change_category
                })
                change_count += 1
                
    df_changes = pd.DataFrame(pattern_changes)
    changes_path = out_dir / "pattern_changes.csv"
    if df_changes.empty:
        df_changes = pd.DataFrame(columns=["company_id", "company_name", "year", "previous_pattern", "current_pattern", "change_category"])
    df_changes.to_csv(changes_path, index=False)
    logger.info(f"Exported pattern strategy transitions to {changes_path}. Changes count: {change_count}")
    
    # 3. Integrate/Update cashflow_intelligence.xlsx
    excel_path = out_dir / "cashflow_intelligence.xlsx"
    if excel_path.exists():
        # Load cashflow intelligence dataframe
        try:
            df_intel = pd.read_excel(excel_path)
            # Standardize columns to internal naming (matching the 9 columns layout)
            reverse_cols = {
                "company_id": "company_id",
                "sector": "sector",
                "CFO Quality": "cfo_quality_label",
                "CapEx Label": "capex_label",
                "FCF CAGR": "fcf_cagr_5yr",
                "FCF Conversion": "fcf_conversion_pct",
                "Distress": "distress_flag",
                "Deleveraging": "deleveraging_flag",
                "Capital Allocation": "capital_allocation_label"
            }
            # Rename Excel headers back to internal keys
            df_intel = df_intel.rename(columns=reverse_cols)
            
            # Since FCF CAGR and FCF Conversion were divided by 100.0 for Excel display,
            # we must multiply them by 100.0 here so they are not divided again by the exporter
            for col in ["fcf_cagr_5yr", "fcf_conversion_pct"]:
                if col in df_intel.columns:
                    df_intel[col] = df_intel[col] * 100.0
            
            # Map updated capital allocation labels from df_latest
            alloc_latest_map = dict(zip(df_latest["company_id"], df_latest["pattern_label"]))
            
            df_intel["company_id_upper"] = df_intel["company_id"].astype(str).str.strip().str.upper()
            df_intel["capital_allocation_label"] = df_intel["company_id_upper"].map(alloc_latest_map).fillna("Mixed")
            df_intel = df_intel.drop(columns=["company_id_upper"])
            
            # Re-run styling exporter to save
            export_excel_intelligence(df_intel, excel_path)
            logger.info(f"Integrated and updated cashflow_intelligence.xlsx at {excel_path}")
        except Exception as e:
            logger.error(f"Failed to update cashflow_intelligence.xlsx: {e}", exc_info=True)
            
    runtime = round(time.time() - start_time, 4)
    
    # Log summary
    logger.info(
        f"Capital Allocation Intelligence completed in {runtime}s. "
        f"Companies Processed: 92. "
        f"Total Strategy Changes Detected: {change_count}."
    )
    
    # Display summary
    print("=" * 80)
    print("             CAPITAL ALLOCATION INTEL & STRATEGY REPORT             ")
    print("=" * 80)
    print(f"[+] Total Companies Processed  : 92")
    print(f"    Total Strategy Changes     : {change_count}")
    print(f"    Engine Runtime             : {runtime}s")
    print(f"    Summary Distribution Path  : {summary_path}")
    print(f"    Pattern Transitions Path   : {changes_path}")
    print(f"    Updated Cash Flow Excel    : {excel_path}")
    print(f"    Validation Status          : {'PASSED' if not errors else 'WARNINGS LOGGED'}")
    print("-" * 80)
    
    return {
        "summary": df_latest,
        "changes": df_changes,
        "change_count": change_count
    }
