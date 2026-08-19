"""
Tearsheet PDF Generator.
Loads data, invokes chart routines, builds ReportLab flowables, and compiles the final PDF.
"""

import sqlite3
import time
from pathlib import Path
from typing import Any

import pandas as pd
from reportlab.lib import colors

# ReportLab imports
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Image as RLImage
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# Package relative imports
from src.config.settings import BASE_DIR, DB_PATH
from src.reports.charts import (
    generate_balancesheet_composition_chart,
    generate_cashflow_waterfall_chart,
    generate_revenue_net_profit_charts,
    generate_roe_roce_chart,
)
from src.reports.layouts import NumberedCanvas
from src.reports.styles import (
    CON_RED,
    GREY_SLATE,
    NAVY_PRIMARY,
    PRINTABLE_WIDTH,
    PRO_GREEN,
    TEXT_LIGHT,
    badge_style,
    bullet_style,
    kpi_label_style,
    kpi_unit_style,
    kpi_value_style,
    meta_style,
    meta_subtitle_style,
    section_heading_style,
    subtitle_style,
    title_style,
)
from src.utils.helpers import extract_year_int
from src.utils.logger import get_logger

# Set up logging
logger = get_logger("tearsheet")

# Badge color mappings
BADGE_COLORS = {
    "Reinvestor": ("#E8F5E9", "#2E7D32", "REINVESTOR"),
    "Shareholder Returns": ("#E8EAF6", "#1A237E", "SHAREHOLDER RETURNS"),
    "Cash Accumulator": ("#E3F2FD", "#0D47A1", "CASH ACCUMULATOR"),
    "Distress Signal": ("#FFEBEE", "#B71C1C", "DISTRESS SIGNAL"),
    "Growth Funded by Debt": ("#FFF3E0", "#E65100", "GROWTH FUNDED BY DEBT"),
    "Liquidating Assets": ("#EFEBE9", "#4E342E", "LIQUIDATING ASSETS"),
    "Pre-Revenue": ("#ECEFF1", "#37474F", "PRE-REVENUE"),
    "Mixed": ("#E0F7FA", "#006064", "MIXED"),
}


# --- STEP 3: Loaders ---


def load_company(company_id: str, db_path: Path | None = None) -> dict[str, Any]:
    """Load company."""
    db_file = db_path or DB_PATH
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    try:
        c = conn.cursor()
        c.execute(
            """
            SELECT c.*, s.broad_sector, s.sub_sector, s.market_cap_category 
            FROM companies c
            LEFT JOIN sectors s ON c.id = s.company_id
            WHERE c.id = ?
        """,
            (company_id,),
        )
        row = c.fetchone()
        if not row:
            raise ValueError(f"Company {company_id} not found in database.")
        return dict(row)
    finally:
        conn.close()


def load_ratios(company_id: str, db_path: Path | None = None) -> pd.DataFrame:
    """Load ratios."""
    db_file = db_path or DB_PATH
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    try:
        c = conn.cursor()
        c.execute(
            """
            SELECT * FROM financial_ratios 
            WHERE company_id = ? AND year != 'TTM'
        """,
            (company_id,),
        )
        rows = c.fetchall()
        df = pd.DataFrame([dict(r) for r in rows])
        if df.empty:
            raise ValueError(f"No ratios data found for company {company_id}")
        df["year_int"] = df["year"].apply(extract_year_int)
        df = df.dropna(subset=["year_int"]).sort_values("year_int").copy()
        if len(df) < 3:
            logger.warning(
                f"Company {company_id} has only {len(df)} years of data (< 3 required)."
            )
        return df
    finally:
        conn.close()


def load_profit_loss(company_id: str, db_path: Path | None = None) -> pd.DataFrame:
    """Load profit loss."""
    db_file = db_path or DB_PATH
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    try:
        c = conn.cursor()
        c.execute(
            """
            SELECT * FROM profitandloss 
            WHERE company_id = ? AND year != 'TTM'
        """,
            (company_id,),
        )
        rows = c.fetchall()
        df = pd.DataFrame([dict(r) for r in rows])
        if df.empty:
            raise ValueError(f"No P&L data found for company {company_id}")
        df["year_int"] = df["year"].apply(extract_year_int)
        df = df.dropna(subset=["year_int"]).sort_values("year_int").copy()
        return df
    finally:
        conn.close()


def load_balance_sheet(company_id: str, db_path: Path | None = None) -> pd.DataFrame:
    """Load balance sheet."""
    db_file = db_path or DB_PATH
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    try:
        c = conn.cursor()
        c.execute(
            """
            SELECT * FROM balancesheet 
            WHERE company_id = ? AND year != 'TTM'
        """,
            (company_id,),
        )
        rows = c.fetchall()
        df = pd.DataFrame([dict(r) for r in rows])
        if df.empty:
            raise ValueError(f"No Balance Sheet data found for company {company_id}")
        df["year_int"] = df["year"].apply(extract_year_int)
        df = df.dropna(subset=["year_int"]).sort_values("year_int").copy()
        return df
    finally:
        conn.close()


def load_cashflow(company_id: str, db_path: Path | None = None) -> pd.DataFrame:
    """Load cashflow."""
    db_file = db_path or DB_PATH
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    try:
        c = conn.cursor()
        c.execute(
            """
            SELECT * FROM cashflow 
            WHERE company_id = ? AND year != 'TTM'
        """,
            (company_id,),
        )
        rows = c.fetchall()
        df = pd.DataFrame([dict(r) for r in rows])
        if df.empty:
            raise ValueError(f"No Cash Flow data found for company {company_id}")
        df["year_int"] = df["year"].apply(extract_year_int)
        df = df.dropna(subset=["year_int"]).sort_values("year_int").copy()
        return df
    finally:
        conn.close()


def load_pros_cons(
    company_id: str, csv_path: Path | None = None
) -> tuple[list[str], list[str]]:
    """Load pros cons."""
    csv_file = csv_path or BASE_DIR / "output" / "pros_cons_generated.csv"
    if not csv_file.exists():
        logger.warning(f"Pros & Cons CSV not found at {csv_file}")
        return [], []
    try:
        df = pd.read_csv(csv_file)
        df_comp = df[
            df["company_id"].astype(str).str.strip().str.upper()
            == str(company_id).strip().upper()
        ].copy()

        pros = (
            df_comp[df_comp["type"] == "PRO"]
            .sort_values(by="confidence_pct", ascending=False)["text"]
            .tolist()
        )
        cons = (
            df_comp[df_comp["type"] == "CON"]
            .sort_values(by="confidence_pct", ascending=False)["text"]
            .tolist()
        )

        return pros, cons
    except Exception as e:
        logger.error(f"Error loading Pros/Cons from CSV: {e}")
        return [], []


def load_capital_allocation(company_id: str, csv_path: Path | None = None) -> str:
    """Load capital allocation."""
    csv_file = csv_path or BASE_DIR / "output" / "capital_allocation.csv"
    if not csv_file.exists():
        logger.warning(f"Capital allocation CSV not found at {csv_file}")
        return "Mixed"
    try:
        df = pd.read_csv(csv_file)
        df_comp = df[
            df["company_id"].astype(str).str.strip().str.upper()
            == str(company_id).strip().upper()
        ].copy()
        if df_comp.empty:
            return "Mixed"
        df_comp["year_int"] = df_comp["year"].apply(extract_year_int)
        df_comp = df_comp.sort_values(by="year_int", ascending=True)
        latest_label = df_comp.iloc[-1]["pattern_label"]
        return latest_label
    except Exception as e:
        logger.error(f"Error loading Capital Allocation from CSV: {e}")
        return "Mixed"


# --- STEP 4: Layout and Header Builder ---


def build_navy_header(company: dict, latest_year: str) -> Table:
    """Creates a custom navy header bar for tearsheet pages."""
    co_name = str(company.get("company_name", "Unknown")).upper()
    ticker = str(company.get("id", "N/A")).upper()
    sector = str(
        company.get("sub_sector") or company.get("broad_sector") or "Unclassified"
    )

    col1_flowables = [
        Paragraph(f"<b>{co_name} ({ticker})</b>", title_style),
        Spacer(1, 2),
        Paragraph(f"Sector Universe: {sector}", subtitle_style),
    ]

    col2_flowables = [
        Paragraph("<b>COMPANY TEARSHEET</b>", meta_style),
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


# --- STEP 5: KPI Card Builder ---


def make_kpi_card(label: str, val_str: str, unit: str, color_hex: str) -> list:
    """Builds the flowable elements for a single KPI Card."""
    label_p = Paragraph(f"<b>{label}</b>", kpi_label_style)
    value_p = Paragraph(
        f"<font color='{color_hex}'><b>{val_str}</b></font>", kpi_value_style
    )
    unit_p = Paragraph(unit, kpi_unit_style)
    return [label_p, Spacer(1, 2), value_p, Spacer(1, 1), unit_p]


def build_kpi_table(ratios_df: pd.DataFrame) -> Table:
    """Creates a 2x3 table of KPI Cards from the latest ratio data."""
    latest_ratio = ratios_df.iloc[-1]

    # 1. ROE
    roe_val = latest_ratio.get("return_on_equity_pct")
    if pd.isnull(roe_val):
        roe_str, roe_color = "N/A", TEXT_LIGHT.hexval()
    else:
        roe_str = f"{roe_val:.1f}%"
        roe_color = (
            PRO_GREEN.hexval()
            if roe_val > 15
            else (CON_RED.hexval() if roe_val < 0 else NAVY_PRIMARY.hexval())
        )
    card_roe = make_kpi_card("Return on Equity (ROE)", roe_str, "Percentage", roe_color)

    # 2. ROCE
    roce_val = latest_ratio.get("return_on_capital_employed_pct")
    if pd.isnull(roce_val):
        roce_str, roce_color = "N/A", TEXT_LIGHT.hexval()
    else:
        roce_str = f"{roce_val:.1f}%"
        roce_color = (
            PRO_GREEN.hexval()
            if roce_val > 15
            else (CON_RED.hexval() if roce_val < 0 else NAVY_PRIMARY.hexval())
        )
    card_roce = make_kpi_card(
        "Return on Capital (ROCE)", roce_str, "Percentage", roce_color
    )

    # 3. NPM
    npm_val = latest_ratio.get("net_profit_margin_pct")
    if pd.isnull(npm_val):
        npm_str, npm_color = "N/A", TEXT_LIGHT.hexval()
    else:
        npm_str = f"{npm_val:.1f}%"
        npm_color = (
            PRO_GREEN.hexval()
            if npm_val > 12
            else (CON_RED.hexval() if npm_val < 0 else NAVY_PRIMARY.hexval())
        )
    card_npm = make_kpi_card(
        "Net Profit Margin (NPM)", npm_str, "Percentage", npm_color
    )

    # 4. Debt to Equity
    de_val = latest_ratio.get("debt_to_equity")
    if pd.isnull(de_val):
        de_str, de_color = "N/A", TEXT_LIGHT.hexval()
    else:
        de_str = f"{de_val:.2f}x"
        # Lower debt is better
        de_color = (
            PRO_GREEN.hexval()
            if de_val < 0.5
            else (CON_RED.hexval() if de_val > 1.5 else NAVY_PRIMARY.hexval())
        )
    card_de = make_kpi_card("Debt to Equity (D/E)", de_str, "Leverage Ratio", de_color)

    # 5. Revenue CAGR (5Y)
    cagr_val = latest_ratio.get("revenue_cagr_5yr")
    if pd.isnull(cagr_val):
        cagr_str, cagr_color = "N/A", TEXT_LIGHT.hexval()
    else:
        cagr_str = f"{cagr_val:.1f}%"
        cagr_color = (
            PRO_GREEN.hexval()
            if cagr_val > 10
            else (CON_RED.hexval() if cagr_val < 0 else NAVY_PRIMARY.hexval())
        )
    card_cagr = make_kpi_card("Revenue CAGR (5Y)", cagr_str, "Growth Rate", cagr_color)

    # 6. FCF
    fcf_val = latest_ratio.get("free_cash_flow_cr")
    if pd.isnull(fcf_val):
        fcf_str, fcf_color = "N/A", TEXT_LIGHT.hexval()
    else:
        fcf_str = f"\u20b9{fcf_val:,.0f} Cr"
        fcf_color = (
            PRO_GREEN.hexval()
            if fcf_val > 0
            else (CON_RED.hexval() if fcf_val < 0 else NAVY_PRIMARY.hexval())
        )
    card_fcf = make_kpi_card(
        "Free Cash Flow (FCF)", fcf_str, "INR in Crores", fcf_color
    )

    # Arrange in a 2x3 Grid Table
    data = [[card_roe, card_roce, card_npm], [card_de, card_cagr, card_fcf]]

    col_w = PRINTABLE_WIDTH / 3.0
    kpi_table = Table(data, colWidths=[col_w, col_w, col_w])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GREY_SLATE),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.white,
                ),  # white grid lines between cards
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return kpi_table


# --- STEP 10: Badge Builder ---


def build_allocation_badge(label: str) -> Table:
    """Builds a beautiful colored capital allocation badge."""
    bg_color, text_color, badge_text = BADGE_COLORS.get(
        label, ("#ECEFF1", "#37474F", str(label).upper())
    )

    badge_para_style = ParagraphStyle(
        "BadgeInner", parent=badge_style, textColor=colors.HexColor(text_color)
    )

    badge_cell = Paragraph(f"<b>{badge_text}</b>", badge_para_style)
    badge_table = Table([[badge_cell]], colWidths=[160])
    badge_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_color)),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 1.2, colors.HexColor(text_color)),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return badge_table


# --- MAIN CONTROLLER ---


def generate_tearsheet(company_id: str, db_path: Path | None = None) -> Path:
    """Generates a professional 2-page tearsheet PDF for the given company."""
    start_time = time.time()
    logger.info(f"[{company_id}] Starting tearsheet generation...")

    # Set up folders
    output_dir = BASE_DIR / "reports"
    tearsheets_dir = output_dir / "tearsheets"
    charts_dir = output_dir / "charts"
    temp_dir = output_dir / "temp"

    for d in [tearsheets_dir, charts_dir, temp_dir]:
        d.mkdir(parents=True, exist_ok=True)

    db_file = db_path or DB_PATH

    # Step 3: Load Data and Validate
    try:
        company = load_company(company_id, db_file)
        ratios_df = load_ratios(company_id, db_file)
        pl_df = load_profit_loss(company_id, db_file)
        bs_df = load_balance_sheet(company_id, db_file)
        cf_df = load_cashflow(company_id, db_file)
        pros, cons = load_pros_cons(company_id)
        alloc_label = load_capital_allocation(company_id)
    except Exception as e:
        logger.error(
            f"[{company_id}] Data loading or validation failed: {e}", exc_info=True
        )
        raise

    latest_year = str(ratios_df.iloc[-1]["year"])

    # Generate Charts
    logger.info(f"[{company_id}] Generating charts...")
    rev_chart, prof_chart = generate_revenue_net_profit_charts(
        pl_df, company_id, charts_dir
    )
    roe_roce_chart = generate_roe_roce_chart(ratios_df, company_id, charts_dir)
    bs_composition_chart = generate_balancesheet_composition_chart(
        bs_df, company_id, charts_dir
    )

    latest_cf_row = cf_df.iloc[-1]
    waterfall_chart = generate_cashflow_waterfall_chart(
        latest_cf_row, company_id, charts_dir
    )

    # Build Story
    logger.info(f"[{company_id}] Compiling ReportLab story...")
    story = []

    # ==================== PAGE 1 ====================
    # 1. Page 1 Header
    page1_header = build_navy_header(company, latest_year)
    story.append(page1_header)
    story.append(Spacer(1, 8))

    # 2. KPI Section
    story.append(Paragraph("<b>KEY FINANCIAL INDICATORS</b>", section_heading_style))
    kpi_cards_table = build_kpi_table(ratios_df)
    story.append(kpi_cards_table)
    story.append(Spacer(1, 8))

    # 3. Revenue & profit Side-by-side charts
    story.append(
        Paragraph("<b>REVENUE & PROFITABILITY TRENDS</b>", section_heading_style)
    )
    rev_img = RLImage(str(rev_chart), width=254, height=147)
    prof_img = RLImage(str(prof_chart), width=254, height=147)
    charts_table1 = Table([[rev_img, prof_img]], colWidths=[261, 261])
    charts_table1.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(charts_table1)
    story.append(Spacer(1, 6))

    # 4. ROE & ROCE Line trend chart
    story.append(
        Paragraph("<b>OPERATIONAL RETURN METRICS (10Y)</b>", section_heading_style)
    )
    line_img = RLImage(str(roe_roce_chart), width=515, height=145)
    story.append(line_img)

    # Page Break strictly after Page 1 content
    story.append(PageBreak())

    # ==================== PAGE 2 ====================
    # 5. Page 2 Header
    page2_header = build_navy_header(company, latest_year)
    story.append(page2_header)
    story.append(Spacer(1, 8))

    # 6. Balance Sheet Stacked Bar & Cash Flow Waterfall Charts Side-by-side
    story.append(
        Paragraph(
            "<b>BALANCE SHEET COMPOSITION & CASH FLOW ANALYSIS</b>",
            section_heading_style,
        )
    )
    bs_img = RLImage(str(bs_composition_chart), width=254, height=147)
    cf_img = RLImage(str(waterfall_chart), width=254, height=147)
    charts_table2 = Table([[bs_img, cf_img]], colWidths=[261, 261])
    charts_table2.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(charts_table2)
    story.append(Spacer(1, 10))

    # 7. Pros & Cons & Capital Allocation Badge
    # Header containing Section Title and Badge side-by-side
    allocation_badge = build_allocation_badge(alloc_label)
    heading_p = Paragraph(
        "<b>FINANCIAL INSIGHTS & NLP SENTIMENT ANALYSIS</b>", section_heading_style
    )

    # Create header table for section 7
    sec7_header_table = Table([[heading_p, allocation_badge]], colWidths=[353, 170])
    sec7_header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(sec7_header_table)
    story.append(Spacer(1, 6))

    # Pros and Cons bullet items (max 4 each to prevent page overflow)
    pros_to_show = pros[:4]
    cons_to_show = cons[:4]

    if not pros_to_show:
        pros_to_show = ["No major financial strengths identified."]
    if not cons_to_show:
        cons_to_show = ["No major financial concerns identified."]

    pros_flowables = [
        Paragraph(
            "<b>Key Financial Strengths (Pros)</b>",
            ParagraphStyle(
                "ProTitle",
                parent=section_heading_style,
                textColor=PRO_GREEN,
                fontSize=10,
                leading=12,
                spaceBefore=0,
                spaceAfter=4,
            ),
        )
    ]
    for p_text in pros_to_show:
        bullet_html = (
            f"<font color='{PRO_GREEN.hexval()}'><b>&#9656;</b></font> {p_text}"
        )
        pros_flowables.append(Paragraph(bullet_html, bullet_style))

    cons_flowables = [
        Paragraph(
            "<b>Key Financial Concerns (Cons)</b>",
            ParagraphStyle(
                "ConTitle",
                parent=section_heading_style,
                textColor=CON_RED,
                fontSize=10,
                leading=12,
                spaceBefore=0,
                spaceAfter=4,
            ),
        )
    ]
    for c_text in cons_to_show:
        bullet_html = f"<font color='{CON_RED.hexval()}'><b>&#9656;</b></font> {c_text}"
        cons_flowables.append(Paragraph(bullet_html, bullet_style))

    pros_cons_table = Table([[pros_flowables, cons_flowables]], colWidths=[256, 256])
    pros_cons_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(pros_cons_table)

    # Compile PDF
    pdf_filename = f"{company_id}_tearsheet.pdf"
    pdf_path = tearsheets_dir / pdf_filename

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=50,
    )

    logger.info(f"[{company_id}] Building PDF at {pdf_path}...")
    doc.build(story, canvasmaker=NumberedCanvas)

    elapsed = time.time() - start_time
    logger.info(f"[{company_id}] Tearsheet generated successfully in {elapsed:.2f}s.")
    return pdf_path


if __name__ == "__main__":
    # Test for one company
    try:
        generate_tearsheet("TCS")
        print("[+] TCS tearsheet generated successfully!")
    except Exception as e:
        print(f"[-] Tearsheet generation failed: {e}")
