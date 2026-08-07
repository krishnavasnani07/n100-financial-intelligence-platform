"""
Sector Report Generator.
Computes median metrics across the 11 standardized sectors and compiles
professional PDF summary reports for constituents.
"""

from __future__ import annotations

import argparse
import datetime
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from reportlab.lib import colors
# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from src.analytics.valuation import load_market_cap
# Custom imports
from src.config.settings import BASE_DIR, DB_PATH, OUTPUT_DIR
from src.reports.layouts import NumberedCanvas
from src.reports.report_utils import check_eligibility, map_sector
from src.reports.styles import (BORDER_LIGHT, CON_RED, GOLD_ACCENT, GREY_SLATE,
                                NAVY_PRIMARY, PRINTABLE_WIDTH, PRO_GREEN,
                                TEXT_LIGHT, TEXT_NEUTRAL, kpi_label_style,
                                kpi_unit_style, kpi_value_style, meta_style,
                                meta_subtitle_style, section_heading_style,
                                subtitle_style, table_cell_bold_style,
                                table_cell_style, table_header_style,
                                title_style)
from src.utils.logger import get_logger

logger = get_logger("sector_report")


def make_sector_kpi_card(label: str, val_str: str, unit: str, color_hex: str) -> list:
    """Builds flowable elements for a sector-level median KPI Card."""
    label_p = Paragraph(f"<b>{label}</b>", kpi_label_style)
    value_p = Paragraph(
        f"<font color='{color_hex}'><b>{val_str}</b></font>", kpi_value_style
    )
    unit_p = Paragraph(unit, kpi_unit_style)
    return [label_p, Spacer(1, 4), value_p, Spacer(1, 2), unit_p]


def build_sector_header(
    sector_name: str, company_count: int, latest_year: str
) -> Table:
    """Creates a custom navy header bar for sector pages."""
    col1_flowables = [
        Paragraph(f"<b>{sector_name.upper()} SECTOR REPORT</b>", title_style),
        Spacer(1, 2),
        Paragraph("Nifty 100 Financial Intelligence Platform", subtitle_style),
    ]

    col2_flowables = [
        Paragraph(f"<b>{company_count} Constituents</b>", meta_style),
        Spacer(1, 2),
        Paragraph(f"Financial Year: {latest_year}", meta_subtitle_style),
    ]

    header_table = Table([[col1_flowables, col2_flowables]], colWidths=[360, 153])
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY_PRIMARY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return header_table


def generate_sector_pdf(
    sector_name: str,
    df_sector: pd.DataFrame,
    medians: Dict[str, float],
    latest_year: str,
    output_path: Path,
) -> None:
    """Generates the Sector PDF report containing Cover Page, Medians, and Constituent Tables."""
    story = []
    company_count = len(df_sector)

    # Sort companies by composite score descending
    df_sorted = df_sector.sort_values(
        by="composite_quality_score", ascending=False
    ).copy()

    # ==================== PAGE 1: COVER & SUMMARY ====================
    # 1. Header
    header = build_sector_header(sector_name, company_count, latest_year)
    story.append(header)
    story.append(Spacer(1, 15))

    # 2. Executive Summary
    summary_text = (
        f"This report presents a comprehensive financial performance breakdown and constituent analysis "
        f"for the <b>{sector_name}</b> sector universe. It profiles <b>{company_count}</b> eligible Nifty 100 "
        f"companies based on the latest financial year (FY{latest_year}) data. The aggregate statistics below represent "
        f"median baseline benchmarks across returns, efficiency, growth, and leverage indices."
    )
    story.append(Paragraph("<b>SECTOR EXECUTIVE SUMMARY</b>", section_heading_style))
    story.append(Paragraph(summary_text, table_cell_style))
    story.append(Spacer(1, 15))

    # 3. Median KPI Cards
    story.append(
        Paragraph("<b>MEDIAN SECTOR PERFORMANCE METRICS</b>", section_heading_style)
    )

    roe_val = medians.get("roe", 0.0)
    roce_val = medians.get("roce", 0.0)
    de_val = medians.get("de", 0.0)
    rev_cagr_val = medians.get("rev_cagr", 0.0)
    pat_cagr_val = medians.get("pat_cagr", 0.0)
    fcf_yield_val = medians.get("fcf_yield", 0.0)

    # Helper formatting for colors
    roe_color = (
        PRO_GREEN.hexval()
        if roe_val > 15
        else (CON_RED.hexval() if roe_val < 0 else NAVY_PRIMARY.hexval())
    )
    roce_color = (
        PRO_GREEN.hexval()
        if roce_val > 15
        else (CON_RED.hexval() if roce_val < 0 else NAVY_PRIMARY.hexval())
    )
    de_color = (
        PRO_GREEN.hexval()
        if de_val < 0.5
        else (CON_RED.hexval() if de_val > 1.5 else NAVY_PRIMARY.hexval())
    )
    rev_color = (
        PRO_GREEN.hexval()
        if rev_cagr_val > 10
        else (CON_RED.hexval() if rev_cagr_val < 0 else NAVY_PRIMARY.hexval())
    )
    pat_color = (
        PRO_GREEN.hexval()
        if pat_cagr_val > 10
        else (CON_RED.hexval() if pat_cagr_val < 0 else NAVY_PRIMARY.hexval())
    )
    fcf_color = (
        PRO_GREEN.hexval()
        if fcf_yield_val > 3.0
        else (CON_RED.hexval() if fcf_yield_val < 0 else NAVY_PRIMARY.hexval())
    )

    card_roe = make_sector_kpi_card(
        "Median ROE", f"{roe_val:.1f}%", "Return on Equity", roe_color
    )
    card_roce = make_sector_kpi_card(
        "Median ROCE", f"{roce_val:.1f}%", "Return on Capital", roce_color
    )
    card_de = make_sector_kpi_card(
        "Median Debt/Equity", f"{de_val:.2f}x", "Leverage Ratio", de_color
    )
    card_rev = make_sector_kpi_card(
        "Median Rev CAGR (5Y)", f"{rev_cagr_val:.1f}%", "Revenue Growth", rev_color
    )
    card_pat = make_sector_kpi_card(
        "Median PAT CAGR (5Y)", f"{pat_cagr_val:.1f}%", "Net Profit Growth", pat_color
    )
    card_fcf = make_sector_kpi_card(
        "Median FCF Yield", f"{fcf_yield_val:.2f}%", "Free Cash Flow / Mcap", fcf_color
    )

    kpis_data = [[card_roe, card_roce, card_de], [card_rev, card_pat, card_fcf]]

    col_w = PRINTABLE_WIDTH / 3.0
    kpis_table = Table(kpis_data, colWidths=[col_w, col_w, col_w])
    kpis_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GREY_SLATE),
                ("GRID", (0, 0), (-1, -1), 1, colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(kpis_table)
    story.append(Spacer(1, 15))

    # Detailed notes
    notes_style = ParagraphStyle(
        "Notes", parent=table_cell_style, fontSize=8, leading=10, textColor=TEXT_LIGHT
    )
    story.append(
        Paragraph(
            "<i>Note: Medians are calculated using eligible constituents within this sector cohort. Financial metrics are winsorized to prevent outlier distortion.</i>",
            notes_style,
        )
    )

    # Page Break before Constituents Table
    story.append(PageBreak())

    # ==================== PAGE 2+: CONSTITUENT COMPANIES ====================
    # 4. Header
    story.append(header)
    story.append(Spacer(1, 15))

    story.append(
        Paragraph("<b>SECTOR CONSTITUENTS BREAKDOWN</b>", section_heading_style)
    )
    story.append(Spacer(1, 5))

    # 5. Build Constituents Table
    headers = [
        Paragraph("<b>Company</b>", table_header_style),
        Paragraph("<b>ROE</b>", table_header_style),
        Paragraph("<b>ROCE</b>", table_header_style),
        Paragraph("<b>Rev CAGR</b>", table_header_style),
        Paragraph("<b>PAT CAGR</b>", table_header_style),
        Paragraph("<b>D/E</b>", table_header_style),
        Paragraph("<b>FCF (Cr)</b>", table_header_style),
        Paragraph("<b>Quality Score</b>", table_header_style),
        Paragraph("<b>Mcap (Cr)</b>", table_header_style),
    ]

    table_data = [headers]

    for idx, row in df_sorted.iterrows():
        # Shorten long company names to make sure they wrap beautifully
        short_name = str(row["company_name"])
        if len(short_name) > 30:
            short_name = short_name[:27] + "..."

        comp_cell = Paragraph(
            f"<b>{row['company_id']}</b><br/><font size='7.5' color='{TEXT_LIGHT.hexval()}'>{short_name}</font>",
            table_cell_style,
        )

        roe_val = row["return_on_equity_pct"]
        roce_val = row["return_on_capital_employed_pct"]
        rev_cagr = row["revenue_cagr_5yr"]
        pat_cagr = row["pat_cagr_5yr"]
        de_val = row["debt_to_equity"]
        fcf_val = row["free_cash_flow_cr"]
        score_val = row["composite_quality_score"]
        mcap_val = row["market_cap_crore"]

        table_data.append(
            [
                comp_cell,
                Paragraph(
                    f"{roe_val:.1f}%" if pd.notnull(roe_val) else "N/A",
                    table_cell_style,
                ),
                Paragraph(
                    f"{roce_val:.1f}%" if pd.notnull(roce_val) else "N/A",
                    table_cell_style,
                ),
                Paragraph(
                    f"{rev_cagr:.1f}%" if pd.notnull(rev_cagr) else "N/A",
                    table_cell_style,
                ),
                Paragraph(
                    f"{pat_cagr:.1f}%" if pd.notnull(pat_cagr) else "N/A",
                    table_cell_style,
                ),
                Paragraph(
                    f"{de_val:.2f}x" if pd.notnull(de_val) else "N/A", table_cell_style
                ),
                Paragraph(
                    f"\u20b9{fcf_val:,.0f}" if pd.notnull(fcf_val) else "N/A",
                    table_cell_style,
                ),
                Paragraph(
                    f"<b>{score_val:.1f}</b>" if pd.notnull(score_val) else "N/A",
                    table_cell_style,
                ),
                Paragraph(
                    f"\u20b9{mcap_val:,.0f}" if pd.notnull(mcap_val) else "N/A",
                    table_cell_style,
                ),
            ]
        )

    # Table Column Widths (totaling 513pt printable area)
    # Ticker, ROE, ROCE, Rev CAGR, PAT CAGR, D/E, FCF, Score, Mcap
    col_widths = [105, 45, 45, 55, 55, 40, 50, 48, 70]

    cons_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    t_style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_PRIMARY),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
    ]

    # Zebra striping
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            t_style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F9FBFD")))

    cons_table.setStyle(TableStyle(t_style))
    story.append(cons_table)

    # Document setup
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=50,
    )

    doc.build(story, canvasmaker=NumberedCanvas)


def generate_all_sector_reports(
    db_path: Optional[Path] = None, out_dir: Optional[Path] = None
) -> None:
    """Computes sectors stats and builds PDF sector reports for all 11 sectors."""
    db_file = db_path or DB_PATH
    output_dir = out_dir or (BASE_DIR / "reports" / "sector")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing Sector summary PDF generation pipeline...")

    # 1. Fetch latest ratios, companies, sectors
    conn = sqlite3.connect(str(db_file))
    query = """
    SELECT 
        fr.company_id,
        c.company_name,
        s.broad_sector,
        s.sub_sector,
        fr.return_on_equity_pct,
        fr.return_on_capital_employed_pct,
        fr.debt_to_equity,
        fr.revenue_cagr_5yr,
        fr.pat_cagr_5yr,
        fr.free_cash_flow_cr,
        fr.composite_quality_score,
        fr.year
    FROM financial_ratios fr
    LEFT JOIN companies c ON fr.company_id = c.id
    LEFT JOIN sectors s ON fr.company_id = s.company_id
    """
    try:
        df_raw = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.critical(f"Failed to fetch data from database: {e}")
        return
    finally:
        conn.close()

    # 2. Extract latest financial records
    from src.utils.helpers import extract_year_int

    df_raw["year_int"] = df_raw["year"].apply(extract_year_int)
    df_raw = df_raw.dropna(subset=["year_int"]).copy()
    df_raw["year_int"] = df_raw["year_int"].astype(int)

    latest_idx = df_raw.groupby("company_id")["year_int"].idxmax()
    df_latest = df_raw.loc[latest_idx].copy()
    latest_year = str(int(df_latest["year_int"].max()))

    # 3. Load latest market cap Excel
    try:
        df_mcap = load_market_cap()
        df_latest = pd.merge(
            df_latest,
            df_mcap[["company_id", "market_cap_crore"]],
            on="company_id",
            how="left",
        )
    except Exception as e:
        logger.error(f"Failed to merge market cap data: {e}")
        df_latest["market_cap_crore"] = np.nan

    # 4. Check eligibility
    eligible_ids = []
    for cid in df_latest["company_id"].unique():
        eligible, _ = check_eligibility(cid, db_file)
        if eligible:
            eligible_ids.append(cid)

    df_eligible = df_latest[df_latest["company_id"].isin(eligible_ids)].copy()
    logger.info(f"Loaded {len(df_eligible)} eligible companies for sector analysis.")

    # 5. Apply dynamic sector mapping
    df_eligible["mapped_sector"] = df_eligible.apply(
        lambda r: map_sector(r["broad_sector"], r["sub_sector"]), axis=1
    )

    # 6. Compute FCF Yield %
    df_eligible["fcf_yield"] = df_eligible.apply(
        lambda r: (
            (r["free_cash_flow_cr"] / r["market_cap_crore"] * 100.0)
            if pd.notnull(r["free_cash_flow_cr"])
            and pd.notnull(r["market_cap_crore"])
            and r["market_cap_crore"] > 0
            else 0.0
        ),
        axis=1,
    )

    # 7. Group and compile
    unique_sectors = sorted(df_eligible["mapped_sector"].unique())
    logger.info(
        f"Identified {len(unique_sectors)} sectors for reporting: {unique_sectors}"
    )

    for sector in unique_sectors:
        df_sec = df_eligible[df_eligible["mapped_sector"] == sector].copy()

        # Calculate Medians
        medians = {
            "roe": df_sec["return_on_equity_pct"].median(),
            "roce": df_sec["return_on_capital_employed_pct"].median(),
            "de": df_sec["debt_to_equity"].median(),
            "rev_cagr": df_sec["revenue_cagr_5yr"].median(),
            "pat_cagr": df_sec["pat_cagr_5yr"].median(),
            "fcf_yield": df_sec["fcf_yield"].median(),
        }

        # Format clean filename
        pdf_name = f"{sector}_report.pdf"
        pdf_path = output_dir / pdf_name

        logger.info(
            f"Generating Sector Report: {pdf_name} with {len(df_sec)} constituents..."
        )
        try:
            generate_sector_pdf(sector, df_sec, medians, latest_year, pdf_path)
            logger.info(f"Successfully generated sector PDF at {pdf_path}")
        except Exception as e:
            logger.error(
                f"Failed to generate report for sector {sector}: {e}", exc_info=True
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Sector Report Generator")
    parser.add_argument("--db", type=str, help="Custom database file path.")
    parser.add_argument(
        "--output", type=str, help="Custom output directory for sector reports."
    )
    args = parser.parse_args()

    db = Path(args.db) if args.db else None
    output = Path(args.output) if args.output else None

    generate_all_sector_reports(db_path=db, out_dir=output)
