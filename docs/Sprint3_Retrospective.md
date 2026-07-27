# Sprint 3 Retrospective — Nifty 100 Financial Intelligence Platform

## 📅 Sprint Details
- **Sprint Goal**: Add interactive visual tools, sector heatmaps, historical trends, a robust two-company peer comparison report generator (Excel and PDF), refactor the screening modules, write automated test cases, and closure.
- **Sprint Status**: **COMPLETED & VERIFIED**

---

## 🎯 Objectives Achieved

| Objective Category | Status | Deliverables Completed |
| :--- | :--- | :--- |
| **Interactive Visualizations** | ✅ Completed | Implemented `src/visualization/radar_chart.py` (single/peer radars), `charts.py` (historical trends), and `heatmaps.py` (sector performance). |
| **Bulk Exporter Setup** | ✅ Completed | Implemented `src/visualization/export.py` to auto-create folders and batch-generate default charts. |
| **Peer Comparison Reports** | ✅ Completed | Implemented Excel generator with embedded radar charts and a ReportLab PDF generator containing styled tables and embedded graphics. |
| **Refactoring & Architecture** | ✅ Completed | Refactored `engine.py` by pulling out helpers into `filters.py` and `utilities.py`; created `src/dashboard/` folder. |
| **QA & Test Coverage** | ✅ Completed | Added 13 new unit/integration tests in `tests/test_visualization.py` and `tests/test_export.py`. All 278 tests are 100% passing. |
| **Clean Repo Closure** | ✅ Completed | Cleaned redundant test CSVs and untracked databases; drafted this retro document. |

---

## 💡 Key Design Decisions & Challenges

1. **Headless Chart Rendering via Agg Backend**:
   - *Challenge*: Pytest execution raised `_tkinter.TclError` due to missing graphical environments for matplotlib's default Tkinter backend.
   - *Solution*: Set `matplotlib.use('Agg')` as the very first import command in all visual files. This forces non-interactive file-rendering, which is stable in command line and server environments.

2. **Current Ratio Calculation Logic**:
   - *Challenge*: The database schema lacked a `current_ratio` field, and balance sheet tables lacked explicit current assets/liabilities.
   - *Solution*: Evaluated values and verified that `other_asset` and `other_liabilities` represent Current Assets and Current Liabilities respectively for firms like TCS and Infosys. Implemented dynamic calculation: `Current Ratio = other_asset / other_liabilities`.

3. **Winsorized Scaling for Spider Charts**:
   - *Challenge*: Raw financial KPIs have highly skewed distributions (e.g. ROE ranging from -50% to +1000%). Linear min-max scaling causes radar charts to collapse.
   - *Solution*: Implemented a winsorized scaling method where values are clipped between the 10th and 90th percentiles of the active universe, then scaled from 0 to 100. Lower-is-better metrics (like Debt-to-Equity) are inverted.

4. **Dynamic Executive Summaries**:
   - *Challenge*: Creating professional summaries that are meaningful and programmatic.
   - *Solution*: Built a rule-based engine categorizing metrics into Growth, Profitability, and Health. The generator counts category-level wins to construct a coherent, human-readable summary.

---

## 🚀 Goals for Next Phase
1. **Interactive Streamlit Dashboard**: Expose these radar charts, trend charts, heatmaps, and report exports via a visual web UI.
2. **REST API Integration**: Build a FastAPI web server layer with Swagger documentation.
3. **Automated Scheduler**: Implement background tasks to refresh historical data.
