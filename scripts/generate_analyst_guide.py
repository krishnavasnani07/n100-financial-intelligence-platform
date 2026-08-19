import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def draw_page_decorations(canvas, doc):
    canvas.saveState()
    # Cover page (page 1) has custom background
    if doc.page == 1:
        # Draw a beautiful dark navy band at the top
        canvas.setFillColor(colors.HexColor("#1B365D"))
        # A4 is 595.27 x 841.89
        canvas.rect(0, 520, 596, 322, fill=True, stroke=False)
        
        # Draw gold accent thin line below navy band
        canvas.setFillColor(colors.HexColor("#D4AF37"))
        canvas.rect(0, 510, 596, 10, fill=True, stroke=False)
        canvas.restoreState()
        return

    # Header on pages 2-11
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.HexColor("#1B365D"))
    canvas.drawString(36, 805, "N100 FINANCIAL INTELLIGENCE PLATFORM")
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#595959"))
    canvas.drawRightString(559, 805, "ANALYST & OPERATIONS GUIDE")
    canvas.setStrokeColor(colors.HexColor("#D9D9D9"))
    canvas.setLineWidth(0.5)
    canvas.line(36, 795, 559, 795)

    # Footer on pages 2-11
    canvas.line(36, 45, 559, 45)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(36, 30, "Confidential - For Internal Analyst Use Only")
    canvas.drawRightString(559, 30, f"Page {doc.page} of 11")
    canvas.restoreState()

def create_analyst_guide(output_path):
    # Setup document template with custom margins
    # topMargin and bottomMargin set to 60pt to avoid content overlapping with header/footer lines
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=60,
        bottomMargin=60
    )
    
    styles = getSampleStyleSheet()
    
    # Custom colors
    navy = colors.HexColor("#1B365D")
    gold = colors.HexColor("#D4AF37")
    charcoal = colors.HexColor("#333333")
    grey_slate = colors.HexColor("#F2F6FA")
    grey_zebra = colors.HexColor("#F9FBFD")
    border_light = colors.HexColor("#D9D9D9")
    text_light = colors.HexColor("#595959")
    
    # Custom styles
    style_cover_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.white,
        spaceAfter=15,
        alignment=0
    )
    
    style_cover_subtitle = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#E0E0E0"),
        spaceAfter=10,
        alignment=0
    )
    
    style_cover_meta = ParagraphStyle(
        "CoverMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=charcoal,
        alignment=0
    )
    
    style_h1 = ParagraphStyle(
        "H1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=navy,
        spaceBefore=10,
        spaceAfter=12,
        keepWithNext=True
    )
    
    style_h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=navy,
        spaceBefore=8,
        spaceAfter=6,
        keepWithNext=True
    )
    
    style_body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=charcoal,
        spaceAfter=8
    )
    
    style_body_bold = ParagraphStyle(
        "BodyBold",
        parent=style_body,
        fontName="Helvetica-Bold"
    )
    
    style_code = ParagraphStyle(
        "CodeBlock",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#A71D5D"),
        backColor=grey_slate,
        borderColor=border_light,
        borderWidth=0.5,
        borderPadding=6,
        spaceAfter=8
    )
    
    style_table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white
    )
    
    style_table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=charcoal
    )
    
    style_table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=style_table_cell,
        fontName="Helvetica-Bold"
    )

    story = []

    # ================= PAGE 1: COVER PAGE =================
    story.append(Spacer(1, 40))
    story.append(Paragraph("N100 FINANCIAL INTELLIGENCE PLATFORM", style_cover_title))
    story.append(Paragraph("Analyst & Operations Guide", style_cover_subtitle))
    story.append(Paragraph("Comprehensive User Manual & Technical Operation Reference", ParagraphStyle("CoverTag", parent=style_cover_subtitle, fontSize=11, textColor=colors.HexColor("#C0C0C0"))))
    
    story.append(Spacer(1, 230))
    
    meta_text = """
    <b>Document Details</b><br/>
    <b>Version:</b> 1.0 (Production Release)<br/>
    <b>Sprint:</b> Sprint 6 — Performance & Integration<br/>
    <b>Date:</b> August 2026<br/>
    <b>Target Universe:</b> Nifty 100 Companies (92 Validated Constituents)<br/>
    <br/>
    <b>Core Technology Stack</b><br/>
    • <b>Language:</b> Python 3.11 / 3.12 (Standard Library)<br/>
    • <b>Data Processing:</b> Pandas, NumPy, OpenPyXL, PyYAML<br/>
    • <b>Relational Engine:</b> SQLite 3 (WAL Mode, Transactional Integrity)<br/>
    • <b>Application Hosting:</b> FastAPI / Uvicorn REST Backend, Streamlit UI Dashboard<br/>
    • <b>Report Generator:</b> ReportLab PDF Compilation Engine<br/>
    • <b>Verification:</b> Pytest Test Suite (211 Tests, 100% Pass)<br/>
    """
    story.append(Paragraph(meta_text, style_cover_meta))
    story.append(PageBreak())

    # ================= PAGE 2: PLATFORM OVERVIEW =================
    story.append(Paragraph("1. Platform Overview", style_h1))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "The Nifty 100 Financial Intelligence Platform is a local-first financial research and analytics engine. "
        "It is designed to automate the process of ingesting raw corporate financial spreadsheets, validating "
        "their content against a set of strict schemas and financial integrity rules, storing the standardized "
        "data in a structured relational database, and exposing the resulting intelligence via programmatic "
        "REST API endpoints and an interactive web-based dashboard.", style_body))
    
    story.append(Paragraph("Core Architecture Pipeline", style_h2))
    story.append(Paragraph(
        "The system coordinates data and control flows through seven primary lifecycle stages:", style_body))
    
    pipeline_data = [
        [Paragraph("Stage", style_table_header), Paragraph("Component", style_table_header), Paragraph("Role & Operation", style_table_header)],
        [Paragraph("1. Ingestion", style_table_cell_bold), Paragraph("ETL Excel Loader", style_table_cell), Paragraph("Parses incoming corporate filing spreadsheets; auto-detects row/column offsets.", style_table_cell)],
        [Paragraph("2. Validation", style_table_cell_bold), Paragraph("DQ Rules Engine", style_table_cell), Paragraph("Applies 16 structural and consistency checks; isolates errors in dedicated logs.", style_table_cell)],
        [Paragraph("3. Storage", style_table_cell_bold), Paragraph("Indexed SQLite DB", style_table_cell), Paragraph("Stores schema-validated data in a normalized database configured in WAL mode.", style_table_cell)],
        [Paragraph("4. Analytics", style_table_cell_bold), Paragraph("KPI & CAGR Engines", style_table_cell), Paragraph("Computes 50+ profitability, liquidity, and growth KPIs with division-by-zero guards.", style_table_cell)],
        [Paragraph("5. PDF Engine", style_table_cell_bold), Paragraph("ReportLab Compiler", style_table_cell), Paragraph("Compiles 2-page company tearsheets and sector summary booklets automatically.", style_table_cell)],
        [Paragraph("6. REST Layer", style_table_cell_bold), Paragraph("FastAPI Server", style_table_cell), Paragraph("Serves 24 versioned JSON routes with autogenerated interactive Swagger docs.", style_table_cell)],
        [Paragraph("7. Interface", style_table_cell_bold), Paragraph("Streamlit Dashboard", style_table_cell), Paragraph("Renders interactive charts, watchlists, and sliding-scale screening presets.", style_table_cell)]
    ]
    t_pipeline = Table(pipeline_data, colWidths=[80, 110, 333])
    t_pipeline.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), navy),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, border_light),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, grey_zebra]),
        ('TOPPADDING', (0,1), (-1,-1), 5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
    ]))
    story.append(t_pipeline)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "By enforcing strict typing, mathematical validation, and relational constraints before presentation, "
        "the platform ensures that financial analysts examine highly accurate datasets free from sheet offset errors "
        "or missing balance-sheet values.", style_body))
    story.append(PageBreak())

    # ================= PAGE 3: INSTALLATION & SETUP =================
    story.append(Paragraph("2. Installation & Environment Setup", style_h1))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "The platform is designed to run locally, eliminating external cloud dependency and ensuring maximum data "
        "privacy. Follow these steps to set up the runtime environment on your local workstation.", style_body))
    
    story.append(Paragraph("1. Codebase Retrieval", style_h2))
    story.append(Paragraph("Clone the version-controlled repository to your local directory:", style_body))
    story.append(Paragraph("git clone https://github.com/krishnavasnani07/n100-financial-intelligence-platform.git<br/>cd n100-financial-intelligence-platform", style_code))
    
    story.append(Paragraph("2. Virtual Environment Configuration", style_h2))
    story.append(Paragraph("Create a sandboxed virtual environment using Python 3.11 or 3.12, then activate it:", style_body))
    story.append(Paragraph("# For Windows Workstations (PowerShell)<br/>python -m venv .venv<br/>.venv\\Scripts\\activate<br/><br/># For macOS and Linux Terminals<br/>python -m venv .venv<br/>source .venv/bin/activate", style_code))
    
    story.append(Paragraph("3. Dependency Installation", style_h2))
    story.append(Paragraph("Install the minimal required package dependencies using pip:", style_body))
    story.append(Paragraph("pip install -r requirements.txt", style_code))
    
    story.append(Paragraph("4. Environment Settings (.env)", style_h2))
    story.append(Paragraph(
        "The system reads configurations from a local environment file. Copy the example configuration template "
        "`.env.example` to `.env` in the root folder, and adjust values as needed:", style_body))
    story.append(Paragraph("ENV=development<br/>DEBUG=True<br/>DB_PATH=db/nifty100.db<br/>LOG_LEVEL=INFO<br/>LOG_FILE=logs/app.log", style_code))
    story.append(PageBreak())

    # ================= PAGE 4: RUNNING THE ETL PIPELINE =================
    story.append(Paragraph("3. Running the ETL & Analytics Pipeline", style_h1))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "The ETL (Extract, Transform, Load) pipeline processes raw corporate spreadsheets, standardizes names, "
        "runs data quality checks, inserts valid records into the SQLite database, and computes financial ratios.", style_body))
    
    story.append(Paragraph("1. Pipeline Execution", style_h2))
    story.append(Paragraph("Run the master ETL pipeline using the following command in the project root:", style_body))
    story.append(Paragraph("# Set PYTHONPATH to the current directory to enable internal module routing<br/>$env:PYTHONPATH=\".\"  # Windows PowerShell<br/>export PYTHONPATH=\".\"    # macOS/Linux<br/><br/># Run the loader pipeline<br/>python main.py", style_code))
    
    story.append(Paragraph("2. Pipeline Stages & Operations", style_h2))
    story.append(Paragraph(
        "When `main.py` is executed, the following actions occur in sequence:", style_body))
    
    etl_steps = """
    <b>A. Parsing & Coordinate Alignment:</b> The <i>ExcelLoader</i> parser scans sheets in <code>data/raw/</code>. It automatically identifies structural row and column offsets by searching for anchor keywords (e.g., 'Revenue', 'Equity').<br/>
    <b>B. Name & Ticker Standardization:</b> Tickers are cleaned and matched against a master metadata list (e.g. standardizing NSE formats like <i>TCS.NS</i> to <i>TCS</i>) to prevent duplicate profiles.<br/>
    <b>C. Data Quality Evaluation:</b> The raw dataset is evaluated against 16 structural checks. If a sheet contains critical errors (e.g., $Assets \neq Liabilities$), it is rejected, and an error report is exported to <code>output/parse_failures.csv</code>.<br/>
    <b>D. Relational Storage:</b> Schema-compliant financial data is loaded into the SQLite database under a single database transaction. If any load operation fails, the transaction auto-rolls back to prevent database corruption.<br/>
    <b>E. Analytical Ratios:</b> After ingestion, the system runs mathematical ratio engines to calculate DuPont profitability margins, historical CAGR growth rates, and cash flow indices. The processed ratios are saved in the <i>financial_ratios</i> table.
    """
    story.append(Paragraph(etl_steps, style_body))
    story.append(PageBreak())

    # ================= PAGE 5: RUNNING THE STREAMLIT DASHBOARD =================
    story.append(Paragraph("4. Running the Streamlit Dashboard", style_h1))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "The interactive analytics dashboard provides a clean user interface for equity research. "
        "It queries the cached SQLite database and displays data using responsive Plotly charts.", style_body))
    
    story.append(Paragraph("1. Startup Command", style_h2))
    story.append(Paragraph("Launch the Streamlit web application from your terminal:", style_body))
    story.append(Paragraph("streamlit run app.py --server.port 8501", style_code))
    story.append(Paragraph("Once started, open your web browser and navigate to: <b>http://localhost:8501</b>", style_body))
    
    story.append(Paragraph("2. Dashboard Screens Directory", style_h2))
    story.append(Paragraph("Navigate between the 8 specialized research views via the sidebar menu:", style_body))
    
    screens_data = [
        [Paragraph("Screen Page", style_table_header), Paragraph("Key Features", style_table_header), Paragraph("Primary Usage", style_table_header)],
        [Paragraph("1. Executive Home", style_table_cell_bold), Paragraph("Treemaps, sector distribution charts, and composite rankers.", style_table_cell), Paragraph("Overview of market performance and quality distributions.", style_table_cell)],
        [Paragraph("2. Company Profile", style_table_cell_bold), Paragraph("Margin charts, DuPont breakdown, leverage tables, and watchlists.", style_table_cell), Paragraph("Deep-dive research into a specific company's financial sheets.", style_table_cell)],
        [Paragraph("3. Investment Screener", style_table_cell_bold), Paragraph("10 interactive sliders, 6 predefined strategy presets, CSV export.", style_table_cell), Paragraph("Filtering and identifying stocks matching target parameters.", style_table_cell)],
        [Paragraph("4. Peer Comparison", style_table_cell_bold), Paragraph("Normalized multi-variable radar charts, relative valuations.", style_table_cell), Paragraph("Comparing a stock directly with its closest sector peers.", style_table_cell)],
        [Paragraph("5. Trend Analysis", style_table_cell_bold), Paragraph("10-year historical metrics, YoY changes, CAGR curves.", style_table_cell), Paragraph("Tracking a firm's long-term sales, earnings, and cash trends.", style_table_cell)],
        [Paragraph("6. Sector Analytics", style_table_cell_bold), Paragraph("Interactive bubble plots (Revenue vs. ROE), index weights.", style_table_cell), Paragraph("Analyzing industry structures and finding sector leaders.", style_table_cell)],
        [Paragraph("7. Capital Allocation", style_table_cell_bold), Paragraph("Treemaps grouping allocation profiles (e.g. Dividend Leaders).", style_table_cell), Paragraph("Evaluating how cash flow is reinvested or returned to owners.", style_table_cell)],
        [Paragraph("8. Reports Browser", style_table_cell_bold), Paragraph("Search overlay, PDF viewer, annual filings directory.", style_table_cell), Paragraph("Reviewing local annual report source documents.", style_table_cell)]
    ]
    t_screens = Table(screens_data, colWidths=[110, 200, 213])
    t_screens.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), navy),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, border_light),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, grey_zebra]),
        ('TOPPADDING', (0,1), (-1,-1), 5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
    ]))
    story.append(t_screens)
    story.append(PageBreak())

    # ================= PAGE 6: USING THE SCREENER =================
    story.append(Paragraph("5. Using the Quality Screener", style_h1))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "The Investment Screener helps analysts identify and rank companies that meet custom financial "
        "thresholds. It features interactive sliders and predefined filters.", style_body))
    
    story.append(Paragraph("1. Preset Filtering Strategies", style_h2))
    story.append(Paragraph(
        "The screener includes 6 predefined, sector-adjusted templates that populate the sliding filters:", style_body))
    
    presets_data = [
        [Paragraph("Strategy Preset", style_table_header), Paragraph("Key Parameters Implemented", style_table_header), Paragraph("Target Category", style_table_header)],
        [Paragraph("Quality Compounder", style_table_cell_bold), Paragraph("ROE > 18%, ROCE > 18%, Debt/Equity < 0.5x, positive FCF.", style_table_cell), Paragraph("High return, low leverage firms.", style_table_cell)],
        [Paragraph("Value Pick", style_table_cell_bold), Paragraph("P/E < Sector Median, FCF Yield > 5%, ROE > 12%.", style_table_cell), Paragraph("Undervalued companies with cash.", style_table_cell)],
        [Paragraph("Dividend Champion", style_table_cell_bold), Paragraph("Dividend Yield > 3%, Payout Ratio < 75%, positive cash flows.", style_table_cell), Paragraph("Stable, high-yield cash generators.", style_table_cell)],
        [Paragraph("Growth Accelerator", style_table_cell_bold), Paragraph("Revenue CAGR (3Y) > 15%, PAT CAGR > 15%, OPM > 10%.", style_table_cell), Paragraph("Rapidly expanding businesses.", style_table_cell)],
        [Paragraph("Debt-Free Blue Chip", style_table_cell_bold), Paragraph("Debt/Equity = 0.0x, Market Cap > Large Cap threshold.", style_table_cell), Paragraph("Ultra-stable, conservative firms.", style_table_cell)],
        [Paragraph("Turnaround Watch", style_table_cell_bold), Paragraph("Improving OPM margins, positive FCF, turning profitable.", style_table_cell), Paragraph("Potential recovery candidates.", style_table_cell)]
    ]
    t_presets = Table(presets_data, colWidths=[110, 240, 173])
    t_presets.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), navy),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, border_light),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, grey_zebra]),
        ('TOPPADDING', (0,1), (-1,-1), 5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
    ]))
    story.append(t_presets)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("2. Operational Workflow Step-by-Step", style_h2))
    screener_workflow = """
    <b>Step 1: Open the Screener.</b> Click 'Investment Screener' in the Streamlit sidebar.<br/>
    <b>Step 2: Choose a Strategy or Adjust Sliders.</b> Select one of the presets to automatically adjust the filters, or manually drag the 10 sliding parameters (ROE, ROCE, PE, etc.).<br/>
    <b>Step 3: Filter by Industry.</b> Use the sector checklist multi-select box to isolate companies in a specific sector (e.g. <i>Information Technology</i>).<br/>
    <b>Step 4: Review Ranked Outputs.</b> The platform ranks qualifying companies by their quality scores and displays their metrics in a responsive data table.<br/>
    <b>Step 5: Export Data.</b> Click the 'Export to CSV' or 'Export Excel Report' buttons to download the screen's output for external models.
    """
    story.append(Paragraph(screener_workflow, style_body))
    story.append(PageBreak())

    # ================= PAGE 7: COMPANY PROFILE & TEARSHEETS =================
    story.append(Paragraph("6. Company Profile & Tearsheets", style_h1))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "The Company Profile view provides detailed financial ratios, margin trends, DuPont parameters, "
        "and custom visualizations for individual stocks. It also supports compiling PDF tearsheets.", style_body))
    
    story.append(Paragraph("1. Research Navigation", style_h2))
    story.append(Paragraph(
        "Open 'Company Profile' in the sidebar navigation. Type or select a ticker (e.g., <code>TCS</code>) "
        "in the autocomplete search box. The page will fetch metrics from the SQLite database.", style_body))
    
    story.append(Paragraph("2. Visual Analytics Sections", style_h2))
    analytics_sections = """
    • <b>Margins Breakdown:</b> Compares gross profit, operating profit, and net profit margins over time.<br/>
    • <b>DuPont Decomposition:</b> Breaks down return on equity (ROE) into profit margin, asset turnover, and leverage multiplier.<br/>
    • <b>Balance Sheet Health:</b> Displays leverage and liquidity trends, highlighting debt levels and coverage metrics.
    """
    story.append(Paragraph(analytics_sections, style_body))
    
    story.append(Paragraph("3. PDF Tearsheet Generation", style_h2))
    story.append(Paragraph(
        "To compile a publication-quality PDF report, click the <b>'Generate PDF Tearsheet'</b> button. "
        "The PDF generation pipeline will build a structured 2-page report for the selected stock. "
        "Generated PDFs are saved in: <code>reports/tearsheets/</code>.", style_body))
    story.append(Paragraph("reports/tearsheets/<br/>└── TCS_tearsheet.pdf", style_code))
    
    story.append(Paragraph("4. Batch PDF Generation Pipeline", style_h2))
    story.append(Paragraph(
        "You can run the batch generation script to generate tearsheets for all 92 validated companies "
        "and sector summaries in one run. Execute this script from the project root:", style_body))
    story.append(Paragraph("python src/reports/batch_generator.py", style_code))
    story.append(PageBreak())

    # ================= PAGE 8: FASTAPI REST API GUIDE =================
    story.append(Paragraph("7. FastAPI REST API Guide", style_h1))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "FastAPI exposes the platform's analytical databases through versioned REST endpoints. "
        "This allows external scripts, Python scripts, and third-party tools to fetch data from the SQLite store.", style_body))
    
    story.append(Paragraph("1. Starting the API Server", style_h2))
    story.append(Paragraph("Launch the FastAPI backend server using Uvicorn:", style_body))
    story.append(Paragraph("uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload", style_code))
    
    story.append(Paragraph("2. Interactive Documentation Documentation Links", style_h2))
    story.append(Paragraph("Once started, access interactive UI pages and documentation files:", style_body))
    story.append(Paragraph(
        "• <b>Swagger Interactive UI:</b> <font color='#1B365D'><b>http://localhost:8000/docs</b></font><br/>"
        "• <b>ReDoc Technical View:</b> <font color='#1B365D'><b>http://localhost:8000/redoc</b></font><br/>"
        "• <b>OpenAPI JSON Schema File:</b> <font color='#1B365D'><b>docs/openapi.json</b></font>", style_body))
    
    story.append(Paragraph("3. Core Endpoint References", style_h2))
    story.append(Paragraph("The API includes 24 routes. The primary endpoints are:", style_body))
    
    endpoints_data = [
        [Paragraph("Method", style_table_header), Paragraph("Endpoint Path", style_table_header), Paragraph("Parameters", style_table_header), Paragraph("Description", style_table_header)],
        [Paragraph("GET", style_table_cell_bold), Paragraph("/api/v1/health", style_table_cell), Paragraph("None", style_table_cell), Paragraph("Database health and table row checks.", style_table_cell)],
        [Paragraph("GET", style_table_cell_bold), Paragraph("/api/v1/companies", style_table_cell), Paragraph("sector (optional)", style_table_cell), Paragraph("List of all tickers in database.", style_table_cell)],
        [Paragraph("GET", style_table_cell_bold), Paragraph("/api/v1/companies/{ticker}", style_table_cell), Paragraph("ticker (in path)", style_table_cell), Paragraph("Full profile details and sector metrics.", style_table_cell)],
        [Paragraph("GET", style_table_cell_bold), Paragraph("/api/v1/companies/{ticker}/ratios", style_table_cell), Paragraph("ticker (in path)", style_table_cell), Paragraph("10-year historical ratios and margins.", style_table_cell)],
        [Paragraph("GET", style_table_cell_bold), Paragraph("/api/v1/screener", style_table_cell), Paragraph("min_roe, max_de, etc.", style_table_cell), Paragraph("Filters stocks by parameters.", style_table_cell)],
        [Paragraph("GET", style_table_cell_bold), Paragraph("/api/v1/sectors", style_table_cell), Paragraph("None", style_table_cell), Paragraph("Aggregated metrics across sectors.", style_table_cell)],
        [Paragraph("GET", style_table_cell_bold), Paragraph("/api/v1/peers/{group}", style_table_cell), Paragraph("group (in path)", style_table_cell), Paragraph("Peer ranks and sector medians.", style_table_cell)],
        [Paragraph("GET", style_table_cell_bold), Paragraph("/api/v1/valuation", style_table_cell), Paragraph("None", style_table_cell), Paragraph("Undervalued and premium classifications.", style_table_cell)]
    ]
    t_endpoints = Table(endpoints_data, colWidths=[50, 150, 110, 213])
    t_endpoints.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), navy),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, border_light),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, grey_zebra]),
        ('TOPPADDING', (0,1), (-1,-1), 5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
    ]))
    story.append(t_endpoints)
    story.append(PageBreak())

    # ================= PAGE 9: API REQUEST/RESPONSE EXAMPLES =================
    story.append(Paragraph("8. API Examples", style_h1))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "Below are examples of API requests and responses. Use these templates to configure integrations "
        "with external tools or scripting environments.", style_body))
    
    story.append(Paragraph("1. Health Status Request", style_h2))
    story.append(Paragraph("curl -X GET \"http://localhost:8000/api/v1/health\"", style_code))
    story.append(Paragraph("Expected JSON Response:", style_body))
    story.append(Paragraph("{\n  \"status\": \"healthy\",\n  \"database_connected\": true,\n  \"companies_count\": 92,\n  \"financial_ratios_count\": 1104\n}", style_code))
    
    story.append(Paragraph("2. Company Ratio Profile Request", style_h2))
    story.append(Paragraph("curl -X GET \"http://localhost:8000/api/v1/companies/TCS/ratios\"", style_code))
    story.append(Paragraph("Expected JSON Response Structure:", style_body))
    story.append(Paragraph("{\n  \"ticker\": \"TCS\",\n  \"ratios\": [\n    {\n      \"year\": 2025,\n      \"roe_pct\": 48.2,\n      \"roce_pct\": 56.4,\n      \"debt_to_equity\": 0.02,\n      \"operating_margin_pct\": 26.5,\n      \"net_margin_pct\": 19.8\n    }\n  ]\n}", style_code))
    
    story.append(Paragraph("3. Stock Screener Request", style_h2))
    story.append(Paragraph("curl -G \"http://localhost:8000/api/v1/screener\" \\\n  --data-urlencode \"min_roe=18\" \\\n  --data-urlencode \"max_de=0.5\"", style_code))
    story.append(Paragraph("Expected JSON Response Structure:", style_body))
    story.append(Paragraph("{\n  \"count\": 28,\n  \"results\": [\n    {\n      \"ticker\": \"INFY\",\n      \"name\": \"Infosys Limited\",\n      \"sector\": \"Information Technology\",\n      \"roe_pct\": 29.8,\n      \"debt_to_equity\": 0.08\n    }\n  ]\n}", style_code))
    story.append(PageBreak())

    # ================= PAGE 10: TROUBLESHOOTING OPERATIONS =================
    story.append(Paragraph("9. Troubleshooting operations", style_h1))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "Use this matrix to diagnose and resolve common errors and operational issues "
        "when running the platform.", style_body))
    
    trouble_data = [
        [Paragraph("Observed Problem", style_table_header), Paragraph("Likely Root Cause", style_table_header), Paragraph("Recommended Action", style_table_header)],
        [
            Paragraph("FastAPI won't start", style_table_cell_bold),
            Paragraph("Port 8000 is occupied by another local service.", style_table_cell),
            Paragraph("Identify and stop the process using port 8000, or run the server on a different port: <code>uvicorn src.api.main:app --port 8001</code>.", style_table_cell)
        ],
        [
            Paragraph("Streamlit won't start", style_table_cell_bold),
            Paragraph("The virtual environment is not activated, or dependencies are missing.", style_table_cell),
            Paragraph("Run the activation command (e.g., <code>.venv\\Scripts\\activate</code>) and re-run <code>pip install -r requirements.txt</code>.", style_table_cell)
        ],
        [
            Paragraph("Database error / empty tables", style_table_cell_bold),
            Paragraph("The database path in `.env` is incorrect, or the database hasn't been created.", style_table_cell),
            Paragraph("Verify that <code>DB_PATH=db/nifty100.db</code> in your <code>.env</code> file, and run the ETL script: <code>python main.py</code>.", style_table_cell)
        ],
        [
            Paragraph("Database lock / slow queries", style_table_cell_bold),
            Paragraph("Parallel writes locked the database file.", style_table_cell),
            Paragraph("Ensure SQLite is running in WAL mode (run <code>PRAGMA journal_mode=WAL;</code>). Avoid concurrent write operations.", style_table_cell)
        ],
        [
            Paragraph("Screener yields empty results", style_table_cell_bold),
            Paragraph("Filters are too restrictive.", style_table_cell),
            Paragraph("Widen your parameters (e.g., reduce the minimum ROE requirement or increase the maximum Debt/Equity threshold).", style_table_cell)
        ],
        [
            Paragraph("PDF Tearsheet fails to compile", style_table_cell_bold),
            Paragraph("ReportLab is missing, or the output directories do not exist.", style_table_cell),
            Paragraph("Create the output folders: <code>mkdir reports/tearsheets</code>. Check that ReportLab is installed.", style_table_cell)
        ],
        [
            Paragraph("API returns 404 Not Found", style_table_cell_bold),
            Paragraph("The ticker format is invalid, or the sector name is misspelled.", style_table_cell),
            Paragraph("Confirm the ticker is in the database using <code>/api/v1/companies</code>. Check for capitalization.", style_table_cell)
        ]
    ]
    t_trouble = Table(trouble_data, colWidths=[110, 160, 253])
    t_trouble.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), navy),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, border_light),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, grey_zebra]),
        ('TOPPADDING', (0,1), (-1,-1), 5),
        ('BOTTOMPADDING', (0,1), (-1,-1), 5),
    ]))
    story.append(t_trouble)
    story.append(PageBreak())

    # ================= PAGE 11: DEVELOPER / TECHNICAL REFERENCE =================
    story.append(Paragraph("10. Developer / Technical Reference", style_h1))
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "This reference section outlines the codebase structure, database schema, and test suite conventions.", style_body))
    
    story.append(Paragraph("1. Codebase Architecture Layout", style_h2))
    story.append(Paragraph(
        "• <b>`src/etl/`</b>: Extraction scripts that parse Excel raw data templates.<br/>"
        "• <b>`src/validation/`</b>: Quality assurance rules verifying structural formatting and consistency.<br/>"
        "• <b>`src/database/`</b>: Relational database connection pools, setup schemas, and loading scripts.<br/>"
        "• <b>`src/analytics/`</b>: Core mathematical engines for ratio and CAGR calculations.<br/>"
        "• <b>`src/api/`</b>: FastAPI routers, request schemas, and logging middleware.<br/>"
        "• <b>`src/reports/`</b>: ReportLab canvas configurations for tearsheet and sector digest compiles.<br/>"
        "• <b>`tests/`</b>: Pytest unit, API, and system integration test suite.", style_body))
    
    story.append(Paragraph("2. Database Schema Indexing", style_h2))
    story.append(Paragraph(
        "To support fast, sub-millisecond query responses, the relational SQLite database includes the following indexes:<br/>"
        "• <b>Primary Keys:</b> Auto-indexed tables for fast query lookups by ID.<br/>"
        "• <b>`idx_ratios_company_year`:</b> Composite index on `(company_id, year)` in the `financial_ratios` table.<br/>"
        "• <b>`idx_pl_company_year`:</b> Composite index on `(company_id, year)` in the P&L table.<br/>"
        "• <b>`idx_sectors_company_id`:</b> Index mapping company IDs directly to their sector classifications.", style_body))
    
    story.append(Paragraph("3. Running the Test Suite", style_h2))
    story.append(Paragraph(
        "The platform includes 211 tests. Verify the code quality by running the test suite locally:", style_body))
    story.append(Paragraph("# Set path environment variable<br/>$env:PYTHONPATH=\".\"<br/><br/># Run all tests<br/>pytest tests/ -v<br/><br/># Export test results to an HTML report file<br/>pytest tests/ --html=reports/pytest_report.html", style_code))
    
    # Build document
    doc.build(story, onFirstPage=draw_page_decorations, onLaterPages=draw_page_decorations)
    print(f"Analyst Guide PDF successfully generated at: {output_path}")

if __name__ == "__main__":
    # Ensure docs directory exists
    os.makedirs("docs", exist_ok=True)
    create_analyst_guide("docs/analyst_guide.pdf")
