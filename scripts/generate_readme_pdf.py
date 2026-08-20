import os
import shutil
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_decorations(page_count)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        w, h = 595.28, 841.89
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8.5)
            self.setFillColor(colors.HexColor("#1B365D"))
            self.drawString(54, h - 40, "N100 FINANCIAL INTELLIGENCE PLATFORM")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#7F8C8D"))
            self.drawRightString(w - 54, h - 40, "System README & Getting Started")
            self.setStrokeColor(colors.HexColor("#BDC3C7"))
            self.setLineWidth(0.5)
            self.line(54, h - 45, w - 54, h - 45)
            
        # Footer
        self.setStrokeColor(colors.HexColor("#BDC3C7"))
        self.setLineWidth(0.5)
        self.line(54, 50, w - 54, 50)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#7F8C8D"))
        self.drawString(54, 38, "Confidential - Project Submission Materials")
        self.drawRightString(w - 54, 38, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def clean_markdown_line(line):
    # Remove simple markdown markers for inline styling
    line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
    line = re.sub(r'\*(.*?)\*', r'<i>\1</i>', line)
    line = re.sub(r'`(.*?)`', r'<font face="Courier" color="#C0392B"><b>\1</b></font>', line)
    # Remove markdown link styling [text](url) -> text
    line = re.sub(r'\[(.*?)\]\(.*?\)', r'<b>\1</b>', line)
    # Remove emoji characters at start
    line = re.sub(r'^[⚡🚀🖥️🧪🎯💡✨🧠📁💻🔒📊🏆🤝📝]+', '', line).strip()
    return line

def parse_readme_to_flowables(readme_path, styles):
    navy = colors.HexColor("#1B365D")
    charcoal = colors.HexColor("#2C3E50")
    
    style_h1 = ParagraphStyle(
        "RH1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=navy,
        spaceBefore=14,
        spaceAfter=10,
        keepWithNext=True
    )
    
    style_h2 = ParagraphStyle(
        "RH2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=navy,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )

    style_h3 = ParagraphStyle(
        "RH3",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=charcoal,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    style_body = ParagraphStyle(
        "RBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14.5,
        textColor=colors.HexColor("#34495E"),
        spaceAfter=8
    )
    
    style_bullet = ParagraphStyle(
        "RBullet",
        parent=style_body,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    style_code = ParagraphStyle(
        "RCode",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#2C3E50")
    )
    
    style_table_cell = ParagraphStyle(
        "RTCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#2C3E50")
    )

    style_table_cell_bold = ParagraphStyle(
        "RTCellBold",
        parent=style_table_cell,
        fontName="Helvetica-Bold"
    )

    flowables = []
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip HTML alignments
        if "<div" in stripped or "</div>" in stripped or "<img" in stripped or "align=" in stripped:
            continue
            
        # Code block toggle
        if stripped.startswith("```"):
            if in_code_block:
                # End of code block, append flowable
                code_text = "\n".join(code_lines)
                # Wrap inside a Table to look like a code block card
                t_code = Table([[Paragraph(code_text.replace("\n", "<br/>").replace(" ", "&nbsp;"), style_code)]], colWidths=[487])
                t_code.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8F9FA")),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#BDC3C7")),
                    ('TOPPADDING', (0,0), (-1,-1), 6),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ('LEFTPADDING', (0,0), (-1,-1), 10),
                    ('RIGHTPADDING', (0,0), (-1,-1), 10),
                ]))
                flowables.append(t_code)
                flowables.append(Spacer(1, 8))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
            continue
            
        if in_code_block:
            code_lines.append(line.rstrip('\n'))
            continue
            
        # Table toggle
        if stripped.startswith('|'):
            in_table = True
            table_lines.append(stripped)
            continue
        elif in_table:
            # End of table, compile and format it
            if table_lines:
                # Filter out formatting rows like |:---|
                filtered_rows = [r for r in table_lines if '---' not in r]
                table_data = []
                for row_idx, row in enumerate(filtered_rows):
                    cells = [clean_markdown_line(c.strip()) for c in row.split('|')[1:-1]]
                    row_data = []
                    for cell in cells:
                        st = style_table_cell_bold if row_idx == 0 else style_table_cell
                        row_data.append(Paragraph(cell, st))
                    table_data.append(row_data)
                
                if table_data:
                    num_cols = len(table_data[0])
                    col_w = [487 / num_cols] * num_cols
                    t = Table(table_data, colWidths=col_w)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), navy),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#BDC3C7")),
                        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8F9FA")]),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('TOPPADDING', (0,0), (-1,-1), 5),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                        ('LEFTPADDING', (0,0), (-1,-1), 6),
                        ('RIGHTPADDING', (0,0), (-1,-1), 6),
                    ]))
                    flowables.append(t)
                    flowables.append(Spacer(1, 10))
                table_lines = []
            in_table = False
            
        # Standard headings and lists
        if stripped.startswith("# "):
            title_text = clean_markdown_line(stripped[2:])
            flowables.append(Paragraph(title_text, style_h1))
            # Thin gold line below document title
            t_line = Table([[""]], colWidths=[487])
            t_line.setStyle(TableStyle([
                ('LINEBELOW', (0,0), (-1,-1), 2, colors.HexColor("#D4AF37")),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            flowables.append(t_line)
            flowables.append(Spacer(1, 10))
        elif stripped.startswith("## "):
            sec_text = clean_markdown_line(stripped[3:])
            flowables.append(Paragraph(sec_text, style_h2))
        elif stripped.startswith("### "):
            sub_text = clean_markdown_line(stripped[4:])
            flowables.append(Paragraph(sub_text, style_h3))
        elif stripped.startswith("• ") or stripped.startswith("* ") or stripped.startswith("- "):
            bullet_text = clean_markdown_line(stripped[2:])
            flowables.append(Paragraph(f"• {bullet_text}", style_bullet))
        elif re.match(r'^\d+\.\s', stripped):
            num_text = clean_markdown_line(re.sub(r'^\d+\.\s', '', stripped))
            flowables.append(Paragraph(f"{stripped.split('.')[0]}. {num_text}", style_bullet))
        elif stripped:
            body_text = clean_markdown_line(stripped)
            flowables.append(Paragraph(body_text, style_body))
            
    return flowables

def generate_readme_pdf():
    readme_md = "README.md"
    pdf_dest = "docs/readme.pdf"
    
    if not os.path.exists(readme_md):
        print(f"Error: {readme_md} not found!")
        return
        
    print(f"Parsing {readme_md}...")
    doc = SimpleDocTemplate(
        pdf_dest,
        pagesize=A4,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    flowables = parse_readme_to_flowables(readme_md, styles)
    
    print(f"Building {pdf_dest} with {len(flowables)} flowable blocks...")
    doc.build(flowables, canvasmaker=NumberedCanvas)
    print("README PDF compilation complete!")
    
    # Copy to deliverables
    deliv_dir = "output/final_deliverables"
    os.makedirs(deliv_dir, exist_ok=True)
    shutil.copy(pdf_dest, os.path.join(deliv_dir, "readme.pdf"))
    print(f"Copied to {deliv_dir}/readme.pdf")

if __name__ == "__main__":
    generate_readme_pdf()
