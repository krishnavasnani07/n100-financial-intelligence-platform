"""
Portfolio Summary Report Generator.
Loads all company financial ratios, intelligence data, pros and cons, and valuation flags,
sorts constituents by ticker ascending, and generates a cohesive 92-page PDF report.
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

# Package relative imports
from src.config.settings import BASE_DIR, DB_PATH, OUTPUT_DIR
from src.reports.report_builder import (
    NumberedCanvas,
    build_allocation_valuation_table,
    build_header,
    build_kpi_table,
    build_pros_cons_table,
    build_trend_table,
)
from src.reports.report_styles import (
    A4_HEIGHT,
    A4_WIDTH,
    MARGIN_POINTS,
    PRINTABLE_WIDTH,
    section_heading_style,
)
from src.reports.report_utils import map_sector, validate_pdf
from src.utils.helpers import extract_year_int
from src.utils.logger import get_logger

# Set up logger
logger = get_logger("portfolio_summary")


def load_all_data(
    db_path: Path,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads database tables and output files required for the portfolio summary report."""
    logger.info("Loading company details and sector mapping from database...")
    conn = sqlite3.connect(str(db_path))
    try:
        companies_df = pd.read_sql_query("SELECT id, company_name FROM companies", conn)
        sectors_df = pd.read_sql_query(
            "SELECT company_id, broad_sector, sub_sector FROM sectors", conn
        )
        ratios_df = pd.read_sql_query(
            "SELECT * FROM financial_ratios WHERE year != 'TTM'", conn
        )
    finally:
        conn.close()

    # Process keys
    companies_df["id"] = companies_df["id"].astype(str).str.strip().str.upper()
    sectors_df["company_id"] = (
        sectors_df["company_id"].astype(str).str.strip().str.upper()
    )
    ratios_df["company_id"] = (
        ratios_df["company_id"].astype(str).str.strip().str.upper()
    )
    ratios_df["year_int"] = ratios_df["year"].apply(extract_year_int)
    ratios_df = (
        ratios_df.dropna(subset=["year_int"])
        .sort_values(by=["company_id", "year_int"])
        .copy()
    )

    # Load output data
    logger.info(
        "Loading intelligence files (pros/cons, valuation, cashflow intelligence)..."
    )
    pros_cons_file = OUTPUT_DIR / "pros_cons_generated.csv"
    if pros_cons_file.exists():
        pros_cons_df = pd.read_csv(pros_cons_file)
        pros_cons_df["company_id"] = (
            pros_cons_df["company_id"].astype(str).str.strip().str.upper()
        )
    else:
        logger.warning(
            f"pros_cons_generated.csv not found at {pros_cons_file}. Using empty default."
        )
        pros_cons_df = pd.DataFrame(
            columns=["company_id", "type", "text", "confidence_pct"]
        )

    val_summary_file = OUTPUT_DIR / "valuation_summary.xlsx"
    if val_summary_file.exists():
        val_df = pd.read_excel(val_summary_file)
        val_df["Company ID"] = val_df["Company ID"].astype(str).str.strip().str.upper()
    else:
        logger.warning(
            f"valuation_summary.xlsx not found at {val_summary_file}. Using empty default."
        )
        val_df = pd.DataFrame(
            columns=[
                "Company ID",
                "P/E Ratio",
                "FCF Yield %",
                "P/E vs. Sector Median %",
                "Valuation Flag",
            ]
        )

    cashflow_intel_file = OUTPUT_DIR / "cashflow_intelligence.xlsx"
    if cashflow_intel_file.exists():
        cf_df = pd.read_excel(cashflow_intel_file)
        cf_df["company_id"] = cf_df["company_id"].astype(str).str.strip().str.upper()
    else:
        logger.warning(
            f"cashflow_intelligence.xlsx not found at {cashflow_intel_file}. Using empty default."
        )
        cf_df = pd.DataFrame(columns=["company_id", "Capital Allocation"])

    return companies_df, sectors_df, ratios_df, pros_cons_df, val_df, cf_df


def validate_portfolio_cohort(
    companies_df: pd.DataFrame,
    sectors_df: pd.DataFrame,
    ratios_df: pd.DataFrame,
    pros_cons_df: pd.DataFrame,
    val_df: pd.DataFrame,
    cf_df: pd.DataFrame,
) -> List[str]:
    """Validates data integrity and logs warnings for missing information."""
    warnings = []

    # 1. Total companies count validation
    comp_ids = set(companies_df["id"].unique())
    if len(comp_ids) != 92:
        warnings.append(
            f"Unexpected company count in database: {len(comp_ids)} (Expected: 92)"
        )

    # 2. Sector mappings validation
    sector_comp_ids = set(sectors_df["company_id"].unique())
    missing_sectors = comp_ids - sector_comp_ids
    if missing_sectors:
        warnings.append(
            f"Missing sector mappings for companies: {list(missing_sectors)}"
        )

    # 3. Ratio KPI validations
    ratio_comp_ids = set(ratios_df["company_id"].unique())
    missing_ratios = comp_ids - ratio_comp_ids
    if missing_ratios:
        warnings.append(
            f"Missing financial ratios data for companies: {list(missing_ratios)}"
        )

    # 4. Valuation data validations
    val_comp_ids = set(val_df["Company ID"].unique())
    missing_val = comp_ids - val_comp_ids
    if missing_val:
        warnings.append(
            f"Missing valuation summary records for companies: {list(missing_val)}"
        )

    # 5. Intelligence data validations
    cf_comp_ids = set(cf_df["company_id"].unique())
    missing_cf = comp_ids - cf_comp_ids
    if missing_cf:
        warnings.append(
            f"Missing cashflow intelligence records for companies: {list(missing_cf)}"
        )

    return warnings


def generate_portfolio_summary_report(db_path: Path) -> Path:
    """Generates the single portfolio_summary.pdf file for all companies."""
    start_time = time.time()
    logger.info("Initializing Portfolio Summary PDF generation pipeline...")

    # Load data
    companies_df, sectors_df, ratios_df, pros_cons_df, val_df, cf_df = load_all_data(
        db_path
    )

    # Validate data
    warnings = validate_portfolio_cohort(
        companies_df, sectors_df, ratios_df, pros_cons_df, val_df, cf_df
    )
    if warnings:
        logger.warning(f"Data validation returned {len(warnings)} warnings:")
        for w in warnings:
            logger.warning(f"  - {w}")
    else:
        logger.info("All portfolio cohort data validations completed successfully.")

    # Create mapping dictionaries for quick lookups
    sector_map = {}
    for _, row in sectors_df.iterrows():
        sector_map[row["company_id"]] = (row["broad_sector"], row["sub_sector"])

    val_map = {}
    for _, row in val_df.iterrows():
        # FCF Yield in valuation summary is FCF Yield %
        val_map[row["Company ID"]] = {
            "pe": row.get("P/E Ratio"),
            "fcf_yield": row.get("FCF Yield %"),
            "sec_median_pe": row.get("5Y Median P/E")
            or row.get("P/E Ratio"),  # Fallback if sector median pe is not named
            "flag": row.get("Valuation Flag") or "Fair",
        }

    # Let's inspect sector median P/E if it has other column name
    # Wait, the columns are: ['Company ID', 'Company Name', 'Sector', 'P/E Ratio', 'P/B Ratio', 'EV/EBITDA', 'FCF Yield %', '5Y Median P/E', 'P/E vs. Sector Median %', 'Valuation Flag']
    # Wait, P/E vs. Sector Median % is computed by Company PE / Sector Median PE * 100.
    # So Sector Median PE = Company PE / (PE vs Sector Median % / 100).
    # Let's compute sector median PE correctly or just fetch it. In valuation.py:
    # df_final has sector_median_pe. But in excel sheet, it is not printed or is renamed.
    # Let's see: `5Y Median P/E` is `5yr_median_PE` from valuation.py which is the 5-year median PE.
    # Sector median PE is `sector_median_pe` in valuation.py. Let's recalculate or load it.
    # Actually, we can read Sector Median PE from DB or recalculate it, or read P/E vs Sector Median % and P/E Ratio.
    # Let's check how valuation_summary.xlsx stores PE Ratio and PE vs Sector Median %:
    # PE vs Sector Median % = PE / Sector Median PE * 100
    # => Sector Median PE = PE / (PE vs Sector Median % / 100)
    # Let's use this formula! It is mathematically exact.
    for cid, val_info in val_map.items():
        pe = val_info["pe"]
        # Find row in val_df
        row = val_df[val_df["Company ID"] == cid].iloc[0]
        pe_vs_sec = row.get("P/E vs. Sector Median %")
        if pd.notnull(pe) and pd.notnull(pe_vs_sec) and pe_vs_sec > 0:
            val_info["sec_median_pe"] = pe / (pe_vs_sec / 100.0)
        else:
            val_info["sec_median_pe"] = None

    cf_map = {}
    for _, row in cf_df.iterrows():
        # Columns in cashflow_intelligence.xlsx: ['company_id', 'sector', 'CFO Quality', 'CapEx Label', 'FCF CAGR', 'FCF Conversion', 'Distress', 'Deleveraging', 'Capital Allocation']
        cf_map[row["company_id"]] = row.get("Capital Allocation") or "Mixed"

    # Sort companies alphabetically by ID (NSE Ticker)
    companies_df = companies_df.sort_values(by="id").reset_index(drop=True)
    cohort = companies_df.to_dict("records")

    story = []

    # Process each company
    for idx, company in enumerate(cohort):
        company_id = company["id"]
        company_name = company["company_name"]

        # Get sector mapping
        broad_sec, sub_sec = sector_map.get(
            company_id, ("Unclassified", "Unclassified")
        )
        mapped_sector_name = map_sector(broad_sec, sub_sec)

        logger.info(
            f"[{idx+1}/92] Generating page for {company_id} ({company_name})..."
        )

        # Get financial ratios history
        co_ratios = ratios_df[ratios_df["company_id"] == company_id].copy()

        if co_ratios.empty:
            logger.warning(f"  No ratio history for {company_id}. Using empty series.")
            latest_ratios = pd.Series()
            prev_ratios = pd.Series()
            latest_year = "N/A"
        else:
            latest_ratios = co_ratios.iloc[-1]
            prev_ratios = co_ratios.iloc[-2] if len(co_ratios) >= 2 else pd.Series()
            latest_year = str(latest_ratios.get("year", "N/A"))

        # Get pros & cons
        co_pros = pros_cons_df[
            (pros_cons_df["company_id"] == company_id) & (pros_cons_df["type"] == "PRO")
        ]
        co_cons = pros_cons_df[
            (pros_cons_df["company_id"] == company_id) & (pros_cons_df["type"] == "CON")
        ]

        pros_list = co_pros.sort_values(by="confidence_pct", ascending=False)[
            "text"
        ].tolist()
        cons_list = co_cons.sort_values(by="confidence_pct", ascending=False)[
            "text"
        ].tolist()

        # Get Capital Allocation
        alloc_label = cf_map.get(company_id, "Mixed")

        # Get Valuation details
        val_info = val_map.get(
            company_id,
            {"pe": None, "fcf_yield": None, "sec_median_pe": None, "flag": "Fair"},
        )
        pe_ratio = val_info["pe"]
        fcf_yield = val_info["fcf_yield"]
        sector_median_pe = val_info["sec_median_pe"]
        val_flag = val_info["flag"]

        # Build ReportLab elements for this page
        # 1. Header Table
        header_table = build_header(
            company_name,
            company_id,
            mapped_sector_name,
            sub_sec or broad_sec,
            latest_year,
        )
        story.append(header_table)
        story.append(Spacer(1, 10))

        # 2. KPI Section
        story.append(
            Paragraph("<b>KEY FINANCIAL INDICATORS</b>", section_heading_style)
        )
        kpi_table = build_kpi_table(latest_ratios)
        story.append(kpi_table)
        story.append(Spacer(1, 10))

        # 3. Trend Section
        story.append(
            Paragraph("<b>YEAR-OVER-YEAR TREND INDICATORS</b>", section_heading_style)
        )
        trend_table = build_trend_table(latest_ratios, prev_ratios)
        story.append(trend_table)
        story.append(Spacer(1, 12))

        # 4. Pros & Cons Section
        story.append(
            Paragraph(
                "<b>FINANCIAL INTELLIGENCE: PROS & CONS SENTIMENT</b>",
                section_heading_style,
            )
        )
        pc_table = build_pros_cons_table(pros_list, cons_list)
        story.append(pc_table)
        story.append(Spacer(1, 12))

        # 5. Capital Allocation & Valuation Section
        av_table = build_allocation_valuation_table(
            alloc_label, fcf_yield, pe_ratio, sector_median_pe, val_flag
        )
        story.append(av_table)

        # Add PageBreak between companies, but not for the last company
        if idx < len(cohort) - 1:
            story.append(PageBreak())

    # Build PDF document
    pdf_dir = BASE_DIR / "reports" / "portfolio"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = pdf_dir / "portfolio_summary.pdf"

    logger.info(f"Building final Portfolio Summary PDF at: {pdf_path}...")
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=45,
    )

    doc.build(story, canvasmaker=NumberedCanvas)

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"Portfolio Summary PDF generated successfully in {elapsed}s.")
    return pdf_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Portfolio Summary PDF Generator")
    parser.add_argument("--db", type=str, help="Custom database file path.")
    args = parser.parse_args()
    db = Path(args.db) if args.db else DB_PATH

    try:
        out_path = generate_portfolio_summary_report(db)
        print(f"[+] Success: Portfolio Summary Report generated at {out_path}")

        # Run verification checks
        valid, msg = validate_pdf(out_path, expected_pages=92)
        print(f"[+] Validation: {msg}")
        if not valid:
            print(f"[-] Validation Error: {msg}", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        logger.error(f"Failed to generate Portfolio Summary: {e}", exc_info=True)
        print(f"[-] Error: {e}", file=sys.stderr)
        sys.exit(1)
