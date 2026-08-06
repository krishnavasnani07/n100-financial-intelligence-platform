"""
Styles and theme definitions for N100 Portfolio Summary Report.
Defines colors, fonts, and ReportLab ParagraphStyle objects.
"""

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4

# Custom Color Palette
NAVY_PRIMARY = colors.HexColor("#1B365D")       # Deep primary color
NAVY_LIGHT = colors.HexColor("#2C5282")         # Mid tone blue
GOLD_ACCENT = colors.HexColor("#D4AF37")        # Gold highlights
GREY_SLATE = colors.HexColor("#F8FAFC")         # Very light slate for card backgrounds
BORDER_LIGHT = colors.HexColor("#E2E8F0")       # Border color
PRO_GREEN = colors.HexColor("#2E7D32")          # Soft green for positive indicators
CON_RED = colors.HexColor("#C62828")            # Soft red for negative indicators
TEXT_NEUTRAL = colors.HexColor("#1E293B")       # Dark neutral for body text
TEXT_LIGHT = colors.HexColor("#64748B")         # Muted gray for labels and notes

# Layout dimensions (A4: 595.27 x 841.89 points)
A4_WIDTH, A4_HEIGHT = A4
MARGIN_POINTS = 36.0 # 0.5 inch margins
PRINTABLE_WIDTH = A4_WIDTH - (2 * MARGIN_POINTS)   # 523.27 pt
PRINTABLE_HEIGHT = A4_HEIGHT - (2 * MARGIN_POINTS) # 769.89 pt

# Sample Styles Sheet
_sample_styles = getSampleStyleSheet()

# Custom ParagraphStyles
title_style = ParagraphStyle(
    "DocTitle",
    parent=_sample_styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=17,
    textColor=colors.white,
    spaceAfter=0,
)

subtitle_style = ParagraphStyle(
    "DocSubtitle",
    parent=_sample_styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=11,
    textColor=colors.HexColor("#CBD5E1"),
    spaceAfter=0,
)

meta_style = ParagraphStyle(
    "DocMeta",
    parent=_sample_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    textColor=colors.white,
    spaceAfter=0,
    alignment=2, # Right-aligned
)

meta_subtitle_style = ParagraphStyle(
    "DocMetaSubtitle",
    parent=_sample_styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=11,
    textColor=colors.HexColor("#CBD5E1"),
    spaceAfter=0,
    alignment=2, # Right-aligned
)

section_heading_style = ParagraphStyle(
    "SectionHeading",
    parent=_sample_styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=13,
    textColor=NAVY_PRIMARY,
    spaceBefore=4,
    spaceAfter=4,
    keepWithNext=True,
)

kpi_label_style = ParagraphStyle(
    "KPILabel",
    parent=_sample_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10,
    textColor=TEXT_LIGHT,
    alignment=1, # Centered
)

kpi_value_style = ParagraphStyle(
    "KPIValue",
    parent=_sample_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=15,
    textColor=NAVY_PRIMARY,
    alignment=1, # Centered
)

kpi_unit_style = ParagraphStyle(
    "KPIUnit",
    parent=_sample_styles["Normal"],
    fontName="Helvetica",
    fontSize=7,
    leading=9,
    textColor=TEXT_LIGHT,
    alignment=1, # Centered
)

trend_label_style = ParagraphStyle(
    "TrendLabel",
    parent=_sample_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=7.5,
    leading=9,
    textColor=TEXT_NEUTRAL,
    alignment=1,
)

trend_arrow_style = ParagraphStyle(
    "TrendArrow",
    parent=_sample_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=12,
    alignment=1,
)

bullet_style = ParagraphStyle(
    "BulletText",
    parent=_sample_styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=10.5,
    textColor=TEXT_NEUTRAL,
    spaceAfter=2,
)

bullet_heading_pro = ParagraphStyle(
    "BulletHeadingPro",
    parent=_sample_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=11,
    textColor=PRO_GREEN,
    spaceAfter=4,
)

bullet_heading_con = ParagraphStyle(
    "BulletHeadingCon",
    parent=_sample_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=11,
    textColor=CON_RED,
    spaceAfter=4,
)

badge_style = ParagraphStyle(
    "BadgeText",
    parent=_sample_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=11,
    alignment=1, # Centered
)

val_label_style = ParagraphStyle(
    "ValLabel",
    parent=_sample_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=8,
    leading=10,
    textColor=TEXT_LIGHT,
)

val_value_style = ParagraphStyle(
    "ValValue",
    parent=_sample_styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=11,
    textColor=TEXT_NEUTRAL,
)
