"""
Styles and theme definitions for N100 tearsheets.
Defines colors, fonts, and ReportLab ParagraphStyle objects.
"""

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4

# Custom Colors (HexColor)
NAVY_PRIMARY = colors.HexColor("#1B365D")
GOLD_ACCENT = colors.HexColor("#D4AF37")
GREY_SLATE = colors.HexColor("#F2F6FA")
ZEBRA_STRIDE = colors.HexColor("#F9FBFD")
PRO_GREEN = colors.HexColor("#2E7D32")
CON_RED = colors.HexColor("#C62828")
TEXT_NEUTRAL = colors.HexColor("#333333")
TEXT_LIGHT = colors.HexColor("#595959")
BORDER_LIGHT = colors.HexColor("#D9D9D9")

# Margins and Dimensions (A4: 595.27 x 841.89 points)
A4_WIDTH, A4_HEIGHT = A4
MARGIN_INCHES = 0.5
MARGIN_POINTS = MARGIN_INCHES * 72 # 36 points
PRINTABLE_WIDTH = A4_WIDTH - (2 * MARGIN_POINTS) # 523.27 points
PRINTABLE_HEIGHT = A4_HEIGHT - (2 * MARGIN_POINTS) # 769.89 points

# Get default sample styles
_sample_styles = getSampleStyleSheet()

# Custom ParagraphStyles
title_style = ParagraphStyle(
    "DocTitle",
    parent=_sample_styles["Heading1"],
    fontName="Helvetica-Bold",
    fontSize=18,
    leading=22,
    textColor=colors.white,
    spaceAfter=0,
    alignment=0, # Left-aligned
)

subtitle_style = ParagraphStyle(
    "DocSubtitle",
    parent=_sample_styles["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=13,
    textColor=colors.HexColor("#E0E0E0"),
    spaceAfter=0,
    alignment=0, # Left-aligned
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
    fontSize=10,
    leading=13,
    textColor=colors.HexColor("#E0E0E0"),
    spaceAfter=0,
    alignment=2, # Right-aligned
)

section_heading_style = ParagraphStyle(
    "SectionHeading",
    parent=_sample_styles["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=15,
    textColor=NAVY_PRIMARY,
    spaceBefore=8,
    spaceAfter=5,
    keepWithNext=True,
)

kpi_label_style = ParagraphStyle(
    "KPILabel",
    parent=_sample_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=9,
    leading=11,
    textColor=TEXT_LIGHT,
    alignment=1, # Centered
)

kpi_value_style = ParagraphStyle(
    "KPIValue",
    parent=_sample_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=17,
    textColor=NAVY_PRIMARY,
    alignment=1, # Centered
)

kpi_unit_style = ParagraphStyle(
    "KPIUnit",
    parent=_sample_styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=TEXT_LIGHT,
    alignment=1, # Centered
)

table_header_style = ParagraphStyle(
    "TableHeader",
    parent=_sample_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=9,
    leading=11,
    textColor=colors.white,
)

table_cell_style = ParagraphStyle(
    "TableCell",
    parent=_sample_styles["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=12,
    textColor=TEXT_NEUTRAL,
)

table_cell_bold_style = ParagraphStyle(
    "TableCellBold",
    parent=table_cell_style,
    fontName="Helvetica-Bold",
)

bullet_style = ParagraphStyle(
    "BulletText",
    parent=_sample_styles["Normal"],
    fontName="Helvetica",
    fontSize=8.5,
    leading=11.5,
    textColor=TEXT_NEUTRAL,
    spaceAfter=4,
)

badge_style = ParagraphStyle(
    "BadgeText",
    parent=_sample_styles["Normal"],
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=12,
    alignment=1, # Centered
)

footer_style = ParagraphStyle(
    "FooterText",
    parent=_sample_styles["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=TEXT_LIGHT,
)
