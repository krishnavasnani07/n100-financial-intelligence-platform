"""
AI Insights and PDF Report Generator Engine.
Generates dynamic financial summaries and recommendations, and exports PDF reports.
"""

from __future__ import annotations
import sqlite3
import pandas as pd
from pathlib import Path
from io import BytesIO
from typing import Dict, List, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from src.config.settings import DB_PATH
from src.peer_analysis.comparison import load_raw_ratios_data, extract_year_int


def generate_company_summary(company_id: str, row: Dict[str, any]) -> str:
    """
    Generates a dynamic, professional natural language financial summary for a company.
    """
    roe = row.get("ROE")
    roce = row.get("ROCE")
    de = row.get("Debt to Equity")
    margin = row.get("Operating Margin")
    rev_cagr = row.get("Revenue CAGR")
    pat_cagr = row.get("PAT CAGR")
    sector = row.get("Sector", "its industry")
    score = row.get("Composite Quality Score", 50.0)
    
    # 1. Profitability Segment
    if roe and roe > 20:
        profit_str = f"consistently maintained exceptional profitability with an ROE of {roe}% and ROCE of {roce}%"
    elif roe and roe > 12:
        profit_str = f"demonstrated healthy profitability profile with a solid ROE of {roe}% and ROCE of {roce}%"
    else:
        profit_str = f"recorded moderate profitability with an ROE of {roe}% and ROCE of {roce}%"
        
    # 2. Leverage Segment
    if de is not None:
        if de == 0:
            leverage_str = "conservative, debt-free balance sheet"
        elif de < 0.5:
            leverage_str = f"very conservative leverage structure (Debt-to-Equity of {de})"
        elif de < 1.5:
            leverage_str = f"manageable debt profile (Debt-to-Equity of {de})"
        else:
            leverage_str = f"higher leverage profile (Debt-to-Equity of {de}), which warrants closer monitoring"
    else:
        leverage_str = "stable capital structure"
        
    # 3. Growth & Margin Segment
    margin_str = f"operating margin of {margin}%" if margin else "stable operating margins"
    growth_pieces = []
    if rev_cagr and rev_cagr > 12:
        growth_pieces.append(f"revenue CAGR of {rev_cagr}%")
    if pat_cagr and pat_cagr > 15:
        growth_pieces.append(f"PAT growth CAGR of {pat_cagr}%")
        
    if growth_pieces:
        growth_str = " accompanied by a strong " + " and ".join(growth_pieces)
    else:
        growth_str = " showing steady top-line and bottom-line trends"
        
    summary = (
        f"{company_id} has {profit_str}, backed by a {leverage_str}. "
        f"The company operates in the {sector} sector with an average {margin_str}{growth_str}. "
        f"Overall, its financial profile points to a Composite Quality Score of {score}/100, "
        f"indicating a {'high-quality business model with stable cash flows' if score >= 60 else 'fundamentally sound model with areas for optimization' if score >= 40 else 'volatile profile requiring careful risk assessment'}."
    )
    return summary


def generate_investment_recommendation(company_id: str, row: Dict[str, any], matched_screeners: List[str]) -> str:
    """
    Generates a dynamic investment analysis paragraph.
    """
    score = row.get("Composite Quality Score", 50.0)
    de = row.get("Debt to Equity")
    
    if matched_screeners:
        screeners_str = ", ".join(matched_screeners)
        recommendation = (
            f"**Analysis**: {company_id} satisfies the criteria for the following predefined screeners: **{screeners_str}**. "
            f"This alignment is driven by the company's strong fundamentals, clean capital structures, and/or attractive return ratios. "
        )
    else:
        recommendation = (
            f"**Analysis**: {company_id} does not currently match any of our preset analyst screeners. "
            f"This suggests its current combinations of valuation, growth, or leverage ratios fall outside standard screening benchmarks. "
        )
        
    if score >= 60:
        rec_str = "a strong core compounder candidate for long-term investors seeking high quality and low default risk"
    elif de and de > 1.5:
        rec_str = "a higher-risk play where investors should carefully evaluate debt servicing capability and interest coverage ratios"
    else:
        rec_str = "a hold/watch candidate that requires monitoring margins and growth acceleration before building exposure"
        
    recommendation += (
        f"Technically, the company rates as {rec_str}. "
        f"As with all equity investments, investors should balance these quantitative metrics against current market valuations (P/E, P/B) "
        f"and macroeconomic sector headwinds before allocating capital."
    )
    return recommendation


def get_company_insights_data(company_id: str, db_path: Optional[Path] = None) -> Dict[str, any]:
    """
    Loads company ratios, matches screeners, and generates text insights.
    """
    df = load_raw_ratios_data(db_path)
    df["Sector"] = df["Sector"].fillna("Unclassified")
    df["year_int"] = df["year"].apply(extract_year_int)
    
    df_latest = df.sort_values(by="year_int", ascending=False).drop_duplicates(subset=["Company"], keep="first")
    comp_row = df_latest[df_latest["Company"] == company_id]
    
    if comp_row.empty:
        return {"success": False, "message": f"Company {company_id} not found."}
        
    row_dict = comp_row.iloc[0].to_dict()
    
    # Identify matching screeners using preset definitions
    from src.screener.presets import run_preset, load_screener_master_data
    matched = []
    try:
        master_df = load_screener_master_data(db_path)
        presets = [
            "Quality Compounder", "Value Pick", "Growth Accelerator",
            "Dividend Champion", "Debt-Free Blue Chip", "Turnaround Watch"
        ]
        for name in presets:
            res_df = run_preset(name, master_df)
            if not res_df.empty and company_id in res_df["company_id"].values:
                matched.append(name)
    except Exception as e:
        pass  # Fallback to empty match if database queries fail during preset checks
        
    summary = generate_company_summary(company_id, row_dict)
    recommendation = generate_investment_recommendation(company_id, row_dict, matched)
    
    return {
        "success": True,
        "company_id": company_id,
        "summary": summary,
        "recommendation": recommendation,
        "matched_screeners": matched,
        "ratios": row_dict
    }


def generate_pdf_report(company_id: str, insights: Dict[str, any]) -> BytesIO:
    """
    Compiles a highly professional PDF research report for a company.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles for Financial Report
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#0F172A'),
        alignment=TA_LEFT,
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#64748B'),
        alignment=TA_LEFT,
        spaceAfter=30
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=15,
        spaceAfter=10
    )
    
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#334155'),
        leading=14,
        spaceAfter=15
    )
    
    th_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.white,
        alignment=TA_LEFT
    )
    
    td_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#1E293B'),
        alignment=TA_LEFT
    )
    
    story = []
    
    # Header
    story.append(Paragraph(f"NIFTY 100 RESEARCH PLATFORM", subtitle_style))
    story.append(Paragraph(f"EQUITY RESEARCH REPORT: {company_id}", title_style))
    
    # Divider line
    divider = Table([['']], colWidths=[504])
    divider.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor('#1E3A8A')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 15))
    
    # Section: Company Overview (AI Generated Summary)
    story.append(Paragraph("1. Financial Summary", h2_style))
    story.append(Paragraph(insights["summary"], body_style))
    
    # Section: Ratios Table
    story.append(Paragraph("2. Core Financial Indicators", h2_style))
    
    ratios = insights["ratios"]
    table_data = [
        [Paragraph("Ratio / Indicator", th_style), Paragraph("Value", th_style)],
        [Paragraph("Sector", td_style), Paragraph(str(ratios.get("Sector", "N/A")), td_style)],
        [Paragraph("Return on Equity (ROE %)", td_style), Paragraph(f"{ratios.get('ROE', 'N/A')}%", td_style)],
        [Paragraph("Return on Capital Employed (ROCE %)", td_style), Paragraph(f"{ratios.get('ROCE', 'N/A')}%", td_style)],
        [Paragraph("Operating Margin (%)", td_style), Paragraph(f"{ratios.get('Operating Margin', 'N/A')}%", td_style)],
        [Paragraph("Revenue CAGR (5-Year %)", td_style), Paragraph(f"{ratios.get('Revenue CAGR', 'N/A')}%", td_style)],
        [Paragraph("PAT CAGR (5-Year %)", td_style), Paragraph(f"{ratios.get('PAT CAGR', 'N/A')}%", td_style)],
        [Paragraph("Debt to Equity Ratio", td_style), Paragraph(str(ratios.get("Debt to Equity", "N/A")), td_style)],
        [Paragraph("Interest Coverage Ratio", td_style), Paragraph(str(ratios.get("Interest Coverage", "N/A")), td_style)],
        [Paragraph("Composite Quality Score", td_style), Paragraph(f"{ratios.get('Composite Quality Score', 'N/A')} / 100", td_style)],
    ]
    
    ratio_table = Table(table_data, colWidths=[250, 254])
    ratio_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F8FAFC'), colors.white]),
        ('TOPPADDING', (0,1), (-1,-1), 5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
    ]))
    story.append(ratio_table)
    story.append(Spacer(1, 15))
    
    # Section: Investment Insights & Recommendations
    story.append(Paragraph("3. Investment Thesis", h2_style))
    story.append(Paragraph(insights["recommendation"], body_style))
    
    # Footer disclaimer
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        textColor=colors.HexColor('#94A3B8'),
        spaceBefore=30,
        alignment=TA_CENTER
    )
    story.append(Paragraph("Disclaimer: This report is dynamically generated for informational and screening purposes only and does not constitute financial, investment, or legal advice.", disclaimer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer
