# 📈 Nifty 100 Financial Intelligence Platform

<div align="center">

```text
==============================================================================================
   _  ___ ___ _______   __  ___ ___  ___    ___ ___ _  _   _  _  ___ ___  ___  _  _   ___ 
  | \| |_ _| __|_   _\ \ / / / _ / _ \ / _ \  | __|_ _| \| | /_\| \| / __|_ _| /_\ | | | |   / __|
  | .` || || _|| | |  \ V / | (_) (_) | (_) | | _|| || .` |/ _ \ .` \__ \| | / _ \| |_| |  | (__ 
  |_|\_|___|_|   |_|   |_|   \___/\___/ \___/  |_| |___|_|\_/_/ \_|\_/___/___/_/ \_\___|_|   \___|
==============================================================================================
                      ENTERPRISE FINANCIAL DATA ENGINEERING & KPI ANALYTICS ENGINE
```

[![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-3.14-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![pytest](https://img.shields.io/badge/Tests-234%20Passed-2EA44F?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**An end-to-end, production-grade financial data engineering pipeline, data quality validation framework, and financial KPI analytics engine built for Nifty 100 companies.**

[System Architecture](#-system-architecture) • [Features](#-key-features) • [ETL Pipeline](#-etl-data-pipeline) • [Financial Ratios](#-sprint-2-financial-kpi-analytics-engine) • [Installation](#-installation--getting-started) • [Testing](#-test-suite--quality-assurance)

</div>

---

## 🎯 About the Project

### 💡 Problem Statement
Financial research for Indian equity markets (specifically Nifty 100 constituents) requires processing large, heterogeneous, un-normalized financial datasets spanning multiple financial years across Profit & Loss, Balance Sheet, Cash Flow, and Valuation filings. Manual ingestion introduces date inconsistencies, foreign key mismatches, numerical precision loss, and un-audited ratio computations.

### 🚀 Business Purpose & Goals
The **Nifty 100 Financial Intelligence Platform** is designed to provide institutional-grade financial data processing by:
1. **Automating Multi-Source Excel Ingestion**: Parsing and loading raw Excel filings across 12 distinct datasets into structured dataframes.
2. **Enforcing Strict Data Quality**: Executing 16 automated Data Quality (DQ) checks to prevent corrupted, duplicated, or unlinked records from entering storage.
3. **Relational Database Population**: Ingesting clean datasets into an ACID-compliant SQLite relational schema (`db/nifty100.db`) enforcing Foreign Keys (`PRAGMA foreign_keys = ON;`) and WAL journaling.
4. **Automating KPI Computations**: Computing core profitability, leverage, efficiency, growth, and cash flow ratios (NPM, OPM, ROE, ROCE, ROA, D/E, ICR, Net Debt, Asset Turnover, FCF, CFO Quality, CapEx Intensity, FCF Conversion, Capital Allocation Patterns), applying financial benchmark classifications, cross-checking anomalies, and exporting audit logs (`ratio_calculation_log.csv`, `capital_allocation.csv` & `cashflow_summary.csv`).

---

## 🛠️ Key Features

| Category | Feature | Description | Status |
| :--- | :--- | :--- | :--- |
| **Ingestion** | **Multi-File Excel Loader** | Ingests 12 raw Excel datasets with file validation, extension checks, and schema enforcement | ✅ Production Ready |
| **Normalization** | **Financial String Normalizer** | Standardizes company tickers (`normalize_ticker`) and dates (`normalize_year` into `YYYY-MM`) | ✅ Production Ready |
| **Validation** | **16 DQ Check Suite** | Validates primary keys, unique constraints, FK integrity, balance sheet equilibrium, tax rates, URLs, and coverage | ✅ Production Ready |
| **Database** | **SQLite Relational Engine** | Enforces FK constraints, composite unique indexes, transactional rollbacks, and automated backups (`db/backups/`) | ✅ Production Ready |
| **Audit** | **Load & KPI Audit System** | Exports timestamped execution summaries (`output/audit/load_audit.csv`) and calculation logs | ✅ Production Ready |
| **Analytics** | **Profitability & Solvency Engine** | Computes NPM, OPM, ROE, ROCE, ROA, D/E, ICR, Net Debt, and Asset Turnover with flags & audit logs | ✅ Production Ready |
| **Growth Engine**| **Reusable CAGR Analytics** | Computes 3Y, 5Y, 10Y Revenue, PAT, & EPS CAGR handling 6 edge cases and growth classification | ✅ Production Ready |
| **Cash Flow** | **Cash Flow & Capital Allocation** | Computes FCF, 5Y CFO Quality, CapEx Intensity, FCF Conversion & 8 Capital Allocation Patterns | ✅ Production Ready |
| **Resilience** | **Safe Division & Error Recovery** | Safe mathematical helpers (`safe_divide`), transaction rollback handling, and fallback error handling | ✅ Production Ready |
| **Testing** | **Comprehensive Pytest Suite** | 234 automated unit, integration, recovery, and mock-file tests with 100% pass rate | ✅ Production Ready |


---

## 💻 Technology Stack & Infrastructure

```text
Language              : Python 3.14+
Relational Storage    : SQLite 3.14 (WAL Mode, Foreign Key Constraints Enforced)
Data Processing       : Pandas, Openpyxl, NumPy
Configuration         : Central Ratio & Growth Config (ratio_config.py & growth_config.py)
Testing Framework     : Pytest 9.1+
Logging Engine        : Standard Logging + Dedicated Ratio Engine Logger (logs/ratio_engine.log)
Version Control       : Git & GitHub Actions Ready
```

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                RAW EXCEL INGESTION LAYER                                │
│  [companies] [profitandloss] [balancesheet] [cashflow] [analysis] [documents] ... (12)  │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   ETL & NORMALIZATION                                   │
│            • ExcelLoader (Column Stripping & Header Offset Alignment)                    │
│            • Normalizers (normalize_ticker & normalize_year -> YYYY-MM)                 │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                             DATA QUALITY VALIDATION ENGINE                              │
│         16 DQ Rules (5 Critical Blockers + 11 Non-Blocker Warnings)                     │
│         Outputs: validation_failures.csv, validation_summary.csv, validation_log.txt   │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              RELATIONAL SQLITE DATABASE                                 │
│               db/nifty100.db (Foreign Keys Enabled, Auto-Backups to db/backups/)         │
└───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                    PROFITABILITY, LEVERAGE, GROWTH & CASH FLOW ENGINES                  │
│     src/analytics/ratios.py (NPM, OPM, ROE, ROCE, ROA, D/E, ICR, Net Debt, Asset Turnover) │
│     src/analytics/cagr.py (Revenue, PAT, EPS 3Y/5Y/10Y CAGR Engine & Edge Cases)       │
│     src/analytics/cashflow_kpis.py (FCF, CFO Quality, CapEx Intensity, Allocation Engine) │
│     Outputs: ratio_calculation_log.csv, capital_allocation.csv, cashflow_summary.csv     │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Directory Layout

```text
n100-financial-intelligence-platform/
│
├── README_ASSETS/           # Visual diagrams, banners, and architecture graphics
├── assets/                  # Project assets and media
│
├── data/                    # Multi-stage data lake
│   ├── raw/                 # 12 Raw input Excel spreadsheets
│   ├── processed/           # Transformed intermediate datasets
│   └── external/            # External mappings & lookup files
│
├── db/                      # Database layer
│   ├── schema.sql           # SQLite DDL database schema definitions
│   ├── nifty100.db          # Active SQLite production database
│   └── backups/             # Automated timestamped post-load backups
│
├── docs/                    # Architectural & domain documentation
│   ├── manual_review.md     # 5-company manual spot-check audit documentation
│   ├── financial_formulas.md# Definitive KPI mathematical formula manual
│   ├── financial_notes.md   # Domain analyst considerations & edge-case rules
│   └── sprint1_retrospective.md # Comprehensive Sprint 1 retrospective report
│
├── logs/                    # Operations & audit logs
│   ├── app.log              # Master pipeline execution log
│   └── ratio_engine.log     # Dedicated KPI ratio calculation log
│
├── notebooks/               # EDA & SQL queries
│   ├── exploratory_queries.sql # 10 business SQL exploratory queries
│   └── cashflow_analysis.ipynb # Cash Flow & Capital Allocation visual analysis
│
├── output/                  # Audit & analytics CSV exports
│   ├── audit/               # load_audit.csv database ingestion metrics
│   ├── reports/             # year_coverage.csv coverage analysis
│   ├── validation/          # Data quality failure & summary CSV reports
│   ├── ratio_calculation_log.csv # Itemized KPI computation audit trail
│   ├── ratio_summary.csv    # Aggregated KPI statistics (Avg, Min, Max, Nulls)
│   ├── leverage_ratio_calculation_log.csv # Itemized leverage KPI audit trail
│   ├── leverage_ratio_summary.csv # Aggregated leverage KPI statistics
│   ├── growth_summary.csv   # Company multi-period Revenue/PAT/EPS CAGR summary & labels
│   ├── cagr_statistics.csv  # Edge-case flag count statistics breakdown
│   ├── capital_allocation.csv # Capital allocation 8-pattern matrix (CFO/CFI/CFF)
│   ├── cashflow_summary.csv # Comprehensive Cash Flow KPI evaluation summary
│   └── capital_pattern_statistics.csv # Capital allocation pattern distribution metrics
│
├── reports/                 # Quality assurance verification reports
│   └── manual_review_report.md # Day 6 QA verification summary report
│
├── src/                     # Core application source code
│   ├── analytics/           # KPI calculation engines
│   │   ├── __init__.py
│   │   ├── ratio_base.py    # RatioCalculator base class & RatioResult dataclass
│   │   ├── ratios.py        # Profitability & Leverage ratio engines
│   │   ├── cagr.py          # Generic CAGR Growth Analytics Engine & Edge Cases
│   │   └── cashflow_kpis.py # Cash Flow Analytics & Capital Allocation Classifier
│   ├── config/              # Central application configuration
│   │   ├── settings.py      # Environment variables & path resolution
│   │   ├── ratio_config.py  # KPI benchmarks, tolerances, and formula versions
│   │   ├── growth_config.py # CAGR time windows, metrics, flags, & classification tiers
│   │   └── cashflow_config.py # CFO Quality, CapEx Intensity, & Capital Allocation maps
│   ├── database/            # Database loaders & connection context managers
│   │   ├── connection.py    # Connection factory & FK pragma enforcement
│   │   ├── loader.py        # Relational DatabaseLoader engine
│   │   └── schema.py        # Schema initializer
│   ├── etl/                 # Ingestion & normalization pipelines
│   │   ├── loader.py        # ExcelLoader class
│   │   └── normalizer.py    # Ticker & year string normalizer functions
│   ├── utils/               # Shared logging & helper utilities
│   │   ├── helpers.py
│   │   └── logger.py        # Central logger setup
│   ├── validation/          # Data Quality framework
│   │   ├── dq_rules.py      # 16 modular DQ validation rule functions
│   │   ├── report.py        # Validation CSV report generator
│   │   └── validator.py     # DataValidator orchestrator
│   └── __init__.py
│
├── tests/                   # Pytest automation test suite
│   ├── database/            # Connection, schema, FK enforcement & recovery tests
│   ├── etl/                 # Excel loader & string normalizer tests
│   ├── kpi/                 # Profitability, Leverage, CAGR, and Cash Flow ratio tests
│   └── validation/          # DQ rule unit, integration, and mock file tests
│
├── .env                     # Local environment configuration
├── main.py                  # Full ETL & analytics entrypoint
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

---

## 🗄️ Database Schema & Data Dictionary

The SQLite database (`db/nifty100.db`) implements 11 relational tables enforcing primary keys, foreign keys referencing `companies(id)`, composite unique indexes, and cascade protections:

```sql
-- Core Relational Schema Overview
CREATE TABLE companies (
    id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    bse_code TEXT,
    nse_symbol TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE profitandloss (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    sales REAL,
    operating_profit REAL,
    opm_percentage REAL,
    net_profit REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);

CREATE TABLE balancesheet (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id TEXT NOT NULL,
    year TEXT NOT NULL,
    equity_capital REAL,
    reserves REAL,
    borrowings REAL,
    total_assets REAL,
    FOREIGN KEY(company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE(company_id, year)
);
```

---

## 🔄 Sprint Roadmap & Execution Progress

| Sprint Phase | Module / Task | Key Deliverables | Status |
| :--- | :--- | :--- | :--- |
| **Sprint 1 - Day 1** | Project Setup | Environment setup, `.env`, logging, directory layout | ✅ Completed |
| **Sprint 1 - Day 2** | Ingestion & Normalizer | `ExcelLoader`, `normalize_ticker`, `normalize_year` | ✅ Completed |
| **Sprint 1 - Day 3** | Data Quality Engine | 16 DQ rules, `DataValidator`, validation CSV reports | ✅ Completed |
| **Sprint 1 - Day 4** | SQLite Schema & Loader | `schema.sql`, `DatabaseLoader`, FK enforcement | ✅ Completed |
| **Sprint 1 - Day 5** | Full ETL & Audit | Executed full 12-file ETL, load audit dashboard, auto-backups | ✅ Completed |
| **Sprint 1 - Day 6** | QA Spot Check | 5-company multi-sector manual audit, year coverage CSV | ✅ Completed |
| **Sprint 1 - Day 7** | SQL & Retrospective | 10 business SQL queries, `sprint1_retrospective.md` | ✅ Completed |
| **Sprint 2 - Day 8** | Profitability Ratios | `ratios.py`, `RatioCalculator`, NPM/OPM/ROE/ROCE/ROA, ratio audit CSVs | ✅ Completed |
| **Sprint 2 - Day 9** | Leverage & Efficiency Engine | Debt-to-Equity, Interest Coverage, Net Debt, Asset Turnover, Flags & Unit Tests | ✅ Completed |
| **Sprint 2 - Day 10**| CAGR Growth Analytics | Generic `calculate_cagr`, Revenue/PAT/EPS 3Y/5Y/10Y, 6 Edge Cases, Reports & Tests | ✅ Completed |
| **Sprint 2 - Day 11**| Cash Flow & Allocation Engine | FCF, 5Y CFO Quality, CapEx Intensity, FCF Conversion, 8 Capital Allocation Patterns, Notebook & CSVs | ✅ Completed |


---

## 🛡️ Data Quality Validation Suite

The platform executes **16 automated Data Quality rules** before loading into SQLite:

```text
🔴 CRITICAL BLOCKER RULES
• DQ-01 (Company PK Uniqueness)   : Verifies primary key uniqueness in companies master.
• DQ-02 (Composite Uniqueness)    : Enforces unique (company_id, year) in financial tables.
• DQ-03 (Foreign Key Integrity)   : Guarantees all company_ids exist in master table.
• DQ-07 (Year Format)             : Standardizes years into YYYY-MM format.
• DQ-08 (Ticker Format)           : Validates uppercase alphanumeric ticker syntax.

🟡 WARNING RULES (NON-BLOCKERS)
• DQ-04 (Balance Sheet Balance)   : Validates Total Assets == Total Liabilities.
• DQ-05 (OPM Cross-Check)         : Cross-checks calculated vs reported OPM.
• DQ-06 (Positive Sales)          : Flags non-positive revenue records.
• DQ-09 (Net Cash Flow Sum)       : Checks operating + investing + financing cash flows.
• DQ-10 (Fixed Assets Range)      : Verifies fixed assets <= total assets.
• DQ-11 (Tax Rate Range)          : Flags tax percentages outside [0, 100].
• DQ-12 (Dividend Payout Range)   : Validates dividend payout ranges.
• DQ-13 (URL Format)              : Verifies annual report and website URL formatting.
• DQ-14 (EPS Sign Match)          : Verifies sign alignment between EPS and Net Profit.
• DQ-15 (Balance Sheet Sub-sums)  : Checks asset/liability sub-category additions.
• DQ-16 (Historical Coverage)     : Flags companies with fewer than 5 financial years.
```

---

## 💰 Sprint 2: Financial KPI Analytics Engine

The financial analytics engine (`src/analytics/ratios.py`, `cagr.py`, `cashflow_kpis.py`) computes fundamental profitability, leverage, efficiency, growth, and cash flow metrics:

### 📐 KPI Formulations & Benchmark Classification

![Profitability Ratio Distributions](README_ASSETS/profitability_distribution.png)

1. **Net Profit Margin (NPM)**:
   $$\text{NPM} = \frac{\text{Net Profit}}{\text{Sales Revenue}} \times 100$$
   *Classification*: $\ge 15\%$ Excellent | $\ge 10\%$ Good | $\ge 5\%$ Average | $< 5\%$ Weak

2. **Operating Profit Margin (OPM)**:
   $$\text{OPM} = \frac{\text{Operating Profit}}{\text{Sales Revenue}} \times 100$$
   *Anomaly Logging*: Computes difference against reported raw OPM; logs warning if diff $> 1.0\%$.

3. **Return on Equity (ROE)**:
   $$\text{ROE} = \frac{\text{Net Profit}}{\text{Equity Capital} + \text{Reserves}} \times 100$$
   *Edge Case Handling*: Returns `None` (status: `NON_POSITIVE_EQUITY`) if total equity $\le 0$.

4. **Return on Capital Employed (ROCE)**:
   $$\text{ROCE} = \frac{\text{EBIT}}{\text{Equity Capital} + \text{Reserves} + \text{Borrowings}} \times 100$$
   *Sector Specialization*: Flags financial sector institutions (`is_financial=True`) for relative evaluation.

5. **Return on Assets (ROA)**:
   $$\text{ROA} = \frac{\text{Net Profit}}{\text{Total Assets}} \times 100$$
   *Classification*: $\ge 15\%$ Excellent | $\ge 10\%$ Good | $\ge 5\%$ Average | $< 5\%$ Weak

6. **Debt-to-Equity (D/E)**:
   $$\text{D/E} = \frac{\text{Borrowings}}{\text{Equity Capital} + \text{Reserves}}$$
   *Edge Cases & Flags*: Returns `0.0` if borrowings equal 0; returns `None` if total equity $\le 0$. Sets `high_leverage_flag = True` if D/E $> 5.0$ (Non-Financials).

7. **Interest Coverage Ratio (ICR)**:
   $$\text{ICR} = \frac{\text{Operating Profit} + \text{Other Income}}{\text{Interest Expense}}$$
   *Edge Cases & Flags*: Suppresses to `None` if interest equals 0 and assigns `icr_label = "Debt Free"`. Sets `icr_warning = True` if ICR $< 1.5$.

8. **Net Debt**:
   $$\text{Net Debt} = \text{Borrowings} - \text{Investments}$$
   *Unadjusted Negative Values*: Negative net debt is valid and indicates a net cash surplus position.

9. **Asset Turnover**:
   $$\text{Asset Turnover} = \frac{\text{Sales Revenue}}{\text{Total Assets}}$$
   *Edge Cases*: Returns `None` if Total Assets $\le 0$.

10. **Compound Annual Growth Rate (CAGR) Engine**:
    $$\text{CAGR} = \left[\left(\frac{\text{End Value}}{\text{Start Value}}\right)^{\frac{1}{\text{Years}}} - 1\right] \times 100$$
    *Edge Case Flags*: Handled `VALID` (positive->positive), `DECLINE_TO_LOSS`, `TURNAROUND`, `BOTH_NEGATIVE`, `ZERO_BASE`, and `INSUFFICIENT`.
    *Growth Tiers*: High Growth (>20%), Strong Growth (10-20%), Moderate (5-10%), Slow (0-5%), Declining (<0%).

11. **Cash Flow Analytics & Capital Allocation Engine**:
    - **Free Cash Flow (FCF)**: $\text{CFO} + \text{CFI}$ (Negative FCF is valid and unadjusted).
    - **CFO Quality Score**: $\frac{\text{CFO}}{\text{PAT}}$ (5-Year Average). High (>1.0), Moderate (0.5–1.0), Accrual Risk (<0.5). Suppressed if PAT $\le 0$.
    - **CapEx Intensity**: $\frac{|\text{CFI}|}{\text{Sales}} \times 100$. Asset Light (<3%), Moderate (3–8%), Capital Intensive (>8%). Suppressed if Sales $\le 0$.
    - **FCF Conversion**: $\frac{\text{FCF}}{\text{Operating Profit}}$. Suppressed if Operating Profit $\le 0$.
    - **Capital Allocation Classifier (8 Patterns)**: Evaluates sign matrix $(\text{CFO}, \text{CFI}, \text{CFF})$ to categorize business allocation into Reinvestor, Shareholder Returns, Liquidating Assets, Distress Signal, Growth Funded by Debt, Cash Accumulator, Pre-Revenue, or Mixed.

---

## 📊 Output Audit Reports

Executing the pipeline populates structured CSV reports under `output/`:

- **`output/audit/load_audit.csv`**: Database ingestion summary (Rows Read, Inserted, Rejected, Execution Time).
- **`output/validation/validation_summary.csv`**: High-level pass/fail summary for each DQ check.
- **`output/ratio_calculation_log.csv`**: Itemized calculation log for profitability KPIs.
- **`output/ratio_summary.csv`**: Statistical summary per profitability KPI.
- **`output/leverage_ratio_calculation_log.csv`**: Itemized calculation log for leverage & efficiency KPIs.
- **`output/leverage_ratio_summary.csv`**: Statistical summary per leverage & efficiency KPI.
- **`output/growth_summary.csv`**: Multi-period (3Y, 5Y, 10Y) Revenue, PAT, and EPS CAGR metrics & growth labels.
- **`output/cagr_statistics.csv`**: Count breakdown of CAGR edge case flags across all companies.
- **`output/capital_allocation.csv`**: Matrix of company-year cash flow sign patterns and allocation labels.
- **`output/cashflow_summary.csv`**: Comprehensive Cash Flow KPI metrics (FCF, CFO Quality 5Y, CapEx Intensity, FCF Conversion).
- **`output/capital_pattern_statistics.csv`**: Distribution metrics of 8 capital allocation patterns across Nifty 100 entities.

---

## 🧪 Test Suite & Quality Assurance

The repository features **234 automated unit, integration, and recovery tests** with 100% pass rate:

```bash
python -m pytest tests/ -v
```

### 🎯 Test Breakdown

```text
tests/database/           : 13 Tests (Connections, schemas, FK enforcement, transaction rollbacks)
tests/etl/                : 76 Tests (ExcelLoader error handling, ticker & year normalizers)
tests/validation/         : 61 Tests (16 Data Quality rules, validator integration, mock file edge cases)
tests/kpi/                : 84 Tests (NPM, OPM, ROE, ROCE, ROA, D/E, ICR, Net Debt, Asset Turnover, Revenue/PAT/EPS CAGR 3Y/5Y/10Y, FCF, 5Y CFO Quality, CapEx Intensity, FCF Conversion, 8 Pattern Classifier, CSV exports)
--------------------------------------------------------------------------------------------------------
TOTAL                     : 234 PASSED (100% Pass Rate)
```

---

## ⚙️ Installation & Getting Started

### Prerequisites
- Python 3.14 (or Python 3.8+)
- Git

### Quickstart Guide

1. **Clone Repository**:
   ```bash
   git clone https://github.com/krishnavasnani07/n100-financial-intelligence-platform.git
   cd n100-financial-intelligence-platform
   ```

2. **Initialize Virtual Environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Execute Pipeline (ETL + Validation + DB Load + Ratio Engine)**:
   ```bash
   python main.py
   ```

5. **Run Test Suite**:
   ```bash
   python -m pytest tests/ -v
   ```

---

## 📝 Financial Analyst Notes & Domain Guidance

- **ROE & Financial Leverage**: A high ROE can result from high financial leverage rather than operational excellence. Always cross-examine ROE with Debt-to-Equity and ROCE.
- **Financial Institutions**: Banks (`HDFCBANK`, `ICICIBANK`, `SBIN`) rely on customer deposits as operational working capital; evaluate banking institutions using ROA and Net Interest Margins (NIM).
- **Negative Equity Protection**: In distressed entities with negative total equity, dividing negative profit by negative equity yields a false positive ROE. The ratio engine explicitly returns `None` for non-positive equity.

---

## 👤 Contributors & License

- **Developer**: Krishna Vasnani ([@krishnavasnani07](https://github.com/krishnavasnani07))
- **Project**: Nifty 100 Financial Intelligence Platform (Bluestock Fintech Analytics Internship)
- **License**: MIT License
