# PDF Tearsheet Generator Documentation

The Nifty 100 Financial Intelligence Platform includes a modular PDF tearsheet generator built with **ReportLab** and **Matplotlib**. It automatically compiles key financial ratios, statement trends, capital allocation badges, and NLP sentiment analysis into a compact, print-ready, two-page company summary.

---

## 📂 Package Architecture

The reporting module is structured under `src/reports/` with clean separation of layout, visual themes, data query handlers, and chart drawings:

```
src/
└── reports/
    ├── __init__.py                # Package initialization exporting generate_tearsheet
    ├── styles.py                  # Colors, fonts, and ReportLab ParagraphStyles
    ├── layouts.py                 # NumberedCanvas for dynamic page numbering
    ├── charts.py                  # Matplotlib visual chart generation engines
    ├── tearsheet.py               # Main orchestrator (data loaders & story compiler)
    └── generate_sample_reports.py # Batch compilation and page-count verification script
```

---

## 🎨 Visual Styling and Theme Rules

To ensure a cohesive and premium design system, all tearsheets conform to a curated palette and typography rules defined in `src/reports/styles.py`:

*   **Page Size:** Standard A4 Portrait (`595.27 x 841.89` points).
*   **Margins:** 0.5 inches (`36` points) top, bottom, left, and right, yielding a printable width of `523.27` points.
*   **Primary Theme Colors:**
    *   *Primary Navy:* `#1B365D` (used for header bars, text, primary chart accents).
    *   *Gold Accent:* `#D4AF37` (used for badges and ROCE trend indicators).
    *   *Card Background:* `#F2F6FA` (light blue-slate background for card grids).
    *   *Positive Green:* `#2E7D32` (profitability curves, positive KPIs, pros bullets).
    *   *Negative Red:* `#C62828` (negative values, high leverage warning, cons bullets).
*   **Typography Leading Constraint:** Every custom `ParagraphStyle` incorporates a leading proportional to its `fontSize` (e.g. `fontSize = 18`, `leading = 22`) to guarantee text never overlaps during auto-wrapping.

---

## 📊 Visual Components and Sizing

### Page 1 Layout

1.  **Navy Header Bar:** Full-width table displaying the company name, NSE ticker symbol, broad/sub sector classification, and the target financial year.
2.  **6-Card KPI Grid:** A `2x3` table layout displaying:
    *   Return on Equity (ROE) — color-coded (Green > 15%, Red < 0%).
    *   Return on Capital Employed (ROCE) — color-coded (Green > 15%, Red < 0%).
    *   Net Profit Margin (NPM) — color-coded (Green > 12%, Red < 0%).
    *   Debt to Equity (D/E) — color-coded (Green < 0.5x, Red > 1.5x).
    *   Revenue CAGR (5Y) — color-coded (Green > 10%, Red < 0%).
    *   Free Cash Flow (FCF) — INR in Crores.
3.  **Revenue & Net Profit Bar Charts:** Matplotlib-generated side-by-side charts representing the last 10 years of annual statements. Width: `254` points, Height: `147` points.
4.  **ROE & ROCE Trajectory:** Full-width line chart showing 10-year trend percentages with custom legends and grid alignments. Width: `515` points, Height: `145` points.

### Page 2 Layout

1.  **Balance Sheet Composition:** Stacked bar chart showing Equity (Capital + Reserves), Borrowings, and Other Liabilities across the last 10 years. Width: `254` points, Height: `147` points.
2.  **Cash Flow Waterfall:** Custom floating bar chart for the latest year representing CFO, CFI, CFF, and Net Cash Flow, coloring positive flows green and negative outflows red. Width: `254` points, Height: `147` points.
3.  **Capital Allocation Badge:** Highlighted box next to the section title displaying the latest year's allocation classification (e.g., `REINVESTOR` or `SHAREHOLDER RETURNS`) with matching background fills and border tags.
4.  **NLP Pros & Cons Section:** Side-by-side tables listing up to 4 bullet points of financial strengths (green bullets) and financial concerns (red bullets) parsed from sentiment CSV files.

---

## 🚀 Execution & Verification

### Generate Tearsheet for a Single Company
Import `generate_tearsheet` in Python and execute it with any valid NSE ticker:

```python
from src.reports.tearsheet import generate_tearsheet
pdf_path = generate_tearsheet("TCS")
print(f"Generated PDF saved at: {pdf_path}")
```

### Batch Generate and Verify Page Budgets
Run the sample batch script to compile and verify tearsheets for target test companies (TCS, HDFCBANK, RELIANCE, SUNPHARMA, TATASTEEL):

```bash
python src/reports/generate_sample_reports.py
```

### Run Integration Tests
Execute the pytest suite to verify page counts, file creation, and invalid input handling:

```bash
python -m pytest tests/test_tearsheet.py
```
