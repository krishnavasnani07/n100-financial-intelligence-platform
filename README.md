# Nifty 100 Financial Intelligence Platform

A modular, robust financial data engineering and intelligence pipeline designed to ingest, process, store, and analyze market data for the Nifty 100 companies.

## 📁 Project Architecture

```text
n100-financial-intelligence-platform/
│
├── assets/                  # Visual assets, charts, and media
│
├── data/                    # Multi-stage data lake
│   ├── raw/                 # Raw ingestion layer (Excel files)
│   ├── processed/           # Transformed & cleaned data
│   └── external/            # External lookup and mapping files
│
├── db/                      # Database storage & schemas
│   ├── schema.sql           # SQLite database schema
│   └── nifty100.db          # Active SQLite database file
│
├── docs/                    # Project documentation
│
├── notebooks/               # Research & EDA Jupyter Notebooks
│
├── output/                  # Pipeline outputs
│   ├── audit/               # Data quality audit logs
│   ├── reports/             # Generated PDF/HTML financial reports
│   └── validation/          # Validation schemas and results
│
├── reports/                 # Analysis and presentation artifacts
│
├── src/                     # Source code package
│   ├── config/              # Application configuration
│   │   └── settings.py      # Day 2: Central settings & path resolution
│   ├── etl/                 # Ingestion & Transformation pipelines
│   │   ├── loader.py        # Day 2: Generic Excel loader
│   │   └── normalizer.py    # Day 2: Data normalizers (years/tickers)
│   ├── utils/               # Shared helper functions
│   │   ├── logger.py        # Day 2: Custom logging utility
│   │   └── helpers.py       # Helper functions
│   ├── validation/          # Pydantic validation schemas
│   │   └── validator.py     # Validator placeholder
│   ├── database/            # Database management and query utilities
│   └── __init__.py          # Package initializer
│
├── tests/                   # Test suite
│   ├── etl/                 # ETL unit/integration tests
│   │   ├── test_loader.py   # Day 2: Loader tests
│   │   └── test_normalizer.py # Day 2: Normalizer tests
│   ├── validation/          # Data validation tests
│   └── database/            # Database connection & query tests
│
├── logs/                    # Runtime logs (app.log)
│
├── .env                     # Local environment configurations
├── .gitignore               # Version control ignore lists
├── Makefile                 # Automation shortcuts
├── README.md                # Project documentation
├── requirements.txt         # Project dependencies
└── main.py                  # Pipeline execution entrypoint
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- SQLite3 (built-in with Python)

### Installation

1. Clone this repository to your local workspace.
2. Initialize environment configurations:
   ```bash
   cp .env.example .env  # or rename .env if present
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Or using the automation command:
   ```bash
   make install
   ```

### Running the Pipeline

To run the main initialization and start the pipeline:
```bash
python main.py
```
Or:
```bash
make run
```

### Running Tests

Execute the test suite using `pytest`:
```bash
pytest
```
Or:
```bash
make test
```

## 🛠️ Tech Stack & Utilities

- **Language:** Python 3.14+
- **Database:** SQLite
- **Libraries:** Pandas, Openpyxl, Pytest, python-dotenv

---

## 🔍 Data Quality & Schema Validation Engine

Sprint 1 - Day 3 introduces a comprehensive data quality check suite to ensure data integrity before loading into the SQLite database.

### 🛡️ Implemented Data Quality (DQ) Rules

The engine validates 16 rules classified by severity:

#### 🔴 Critical Rules (Blockers)
- **DQ-01 (Company PK Uniqueness)**: Verifies that company IDs in the master list are unique.
- **DQ-02 (No Duplicate Records)**: Confirms no duplicate `(company_id, year)` entries in Profit & Loss, Balance Sheet, and Cash Flow tables.
- **DQ-03 (Foreign Key Integrity)**: Ensures every `company_id` in other datasets matches a valid company ID in the master list.
- **DQ-07 (Year Format)**: Ensures the year matches the normalized `YYYY-MM` format.
- **DQ-08 (Ticker Format)**: Verifies that company IDs conform to uppercase, alphanumeric, 2-12 character rules.

#### 🟡 Warning Rules (Non-Blockers)
- **DQ-04 (Balance Sheet Balance)**: Validates `total_assets == total_liabilities`.
- **DQ-05 (OPM Cross-Check)**: Verifies calculated Operating Profit Margin against the reported value.
- **DQ-06 (Positive Sales)**: Rejects negative or zero sales in the P&L table.
- **DQ-09 (Net Cash Flow)**: Checks that components sum up to the reported Net Cash Flow.
- **DQ-10 (Fixed Assets Range)**: Confirms fixed assets are non-negative and `<= total_assets`.
- **DQ-11 (Tax Rate)**: Rejects tax percentages outside `[0, 100]`.
- **DQ-12 (Dividend Payout)**: Validates dividend payout range.
- **DQ-13 (URL Format)**: Verifies formatting of website, logo, profiles, and annual report links.
- **DQ-14 (EPS Sign)**: Matches signs of Earnings Per Share and Net Profit.
- **DQ-15 (Balance Sheet Informational Sums)**: Cross-checks BS subcategories match total assets/liabilities.
- **DQ-16 (Coverage)**: Rejects companies with less than 5 years of historical financial records.

### ⚙️ Validation Workflow & Execution

The validator works by loading all 12 raw Excel files, performing string normalizations, executing each rule sequentially, logging failures, and producing CSV reports:

1. **Read & Normalize**: Uses custom parsing to clean tickers and parse years.
2. **Execute Checks**: Runs the 16 validation functions against the dataframes.
3. **Generate Outputs**: Writes three files to `output/validation/`:
   - `validation_failures.csv`: Every individual row failing a validation check.
   - `validation_summary.csv`: Aggregated counts of Passed/Failed rows per rule.
   - `validation_log.txt`: Detailed timestamped audit trail of the run.

### 🏃 How to Run Validation

To run the validation pipeline and view the console report:
```bash
python main.py
```
This prints the validation summary indicating PASS/FAIL for each rule and outputs the results to `output/validation/`.

---

## 💾 Sprint 1 - Day 5: Full Data Load & Database Audit

Sprint 1 - Day 5 connects all ETL components (Loader $\rightarrow$ Normalizer $\rightarrow$ Validator $\rightarrow$ SQLite Loader) into a unified production-ready pipeline.

### 📊 Ingested Relational Table Row Counts

| Relational Table | Source Rows Read | DB Inserted Rows | Rejected Rows | Runtime (sec) | FK Enforced |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **companies** | 92 | 92 | 0 | ~0.018s | Primary Key Master |
| **sectors** | 92 | 92 | 0 | ~0.017s | ✅ Verified |
| **analysis** | 20 | 16 | 4 | ~0.018s | ✅ Verified |
| **prosandcons** | 16 | 14 | 2 | ~0.019s | ✅ Verified |
| **profitandloss** | 1,276 | 1,164 | 112 | ~0.031s | ✅ Verified |
| **balancesheet** | 1,312 | 1,140 | 172 | ~0.031s | ✅ Verified |
| **cashflow** | 1,187 | 1,068 | 119 | ~0.024s | ✅ Verified |
| **documents** | 1,585 | 1,457 | 128 | ~0.025s | ✅ Verified |
| **stock_prices** | 5,520 | 5,520 | 0 | ~0.047s | ✅ Verified |
| **peer_groups** | 56 | 56 | 0 | ~0.015s | ✅ Verified |
| **financial_ratios**| 0 | 0 | 0 | 0s | Reserved (Sprint 2) |
| **TOTAL** | **12,466** | **10,619** | **537** | **~0.24s** | **0 FK Violations** |

### 🔍 Verification & Audit Integrity

- **Database Audit Report**: Automatically written to `output/audit/load_audit.csv` with table name, rows read, inserted, rejected, execution runtime, and timestamps.
- **Foreign Key Check (`PRAGMA foreign_key_check;`)**: Executed post-load, returning **0 constraint violations**.
- **Duplicate Prevention**: Composite key checks `(company_id, year)` return 0 duplicates in `profitandloss`, `balancesheet`, and `cashflow`.
- **Database Smoke Tests**: All relational queries and joins between `companies` and financial tables pass integrity checks cleanly.
- **Automated Database Backups**: Post-load backup snapshots automatically stored under `db/backups/nifty100_YYYYMMDD_HHMMSS.db`.
- **Error Recovery Testing**: Comprehensive test suite (`tests/database/test_error_recovery.py`) verifies pipeline resilience against missing files, empty DataFrames, duplicate PK insertion rollbacks, and FK violation rollbacks.

### 📈 Sprint 1 Progress & Operational Summary

| Metric | Status / Value | Description |
| :--- | :--- | :--- |
| **Excel Source Files Ingested** | 12 / 12 | 100% of target datasets processed |
| **Relational Database Population** | **SUCCESS** | Clean database built at `db/nifty100.db` |
| **Database Tables Populated** | 10 active tables | All 10 core schema tables populated |
| **Total Rows Inserted** | **10,619** | Relational records verified and stored |
| **Total Rows Rejected** | 537 | Logged with reason in audit outputs |
| **Foreign Key Violations** | **0** | Verified via `PRAGMA foreign_key_check;` |
| **Database Backups Generated** | `db/backups/` | Timestamped post-load database copy |
| **Console Monitoring Dashboard** | Included in `main.py` | Operational executive summary rendered on terminal |
| **Test Suite Coverage** | **150 / 150 Passed** | Complete unit, integration, and recovery test suite passing |
| **Sprint 1 Retrospective** | `docs/sprint1_retrospective.md` | Comprehensive retrospective document |

---

## 🔬 Sprint 1 - Day 6 & 7: QA Audit, Exploratory SQL & Sprint Closure

### 🧪 Manual QA Review Audit (Day 6)
- **Sample Companies Evaluated**: `TCS` (IT), `HDFCBANK` (Banking), `ITC` (FMCG), `TATAMOTORS` (Auto), `SUNPHARMA` (Pharma).
- **Audit Documentation**: Recorded in `docs/manual_review.md` and summarized in `reports/manual_review_report.md`.
- **Numeric Precision**: **100% Match** across raw Excel values, normalized dataframes, and SQLite database rows for key fields (Sales, Net Profit, Equity Capital, Total Assets).
- **Year Coverage Report**: Generated at `output/reports/year_coverage.csv` (91/92 companies have $\ge 5$ historical financial years).

### 🔍 Exploratory SQL Query Suite (Day 7)
- **Query Suite Location**: `notebooks/exploratory_queries.sql`
- **10 Core Business Queries**:
  1. Total master companies count.
  2. Sector company distribution.
  3. Financial year record counts.
  4. Top 10 companies by sales revenue (Mar 2023).
  5. Companies with negative net profit.
  6. Companies missing annual report document links.
  7. Industry sector average debt/borrowings.
  8. Top 10 companies by Total Assets.
  9. Aggregated operating, investing, and financing cash flows.
  10. Year coverage details per company.

---

## 📄 Documentation References
- **Data Audit & Manual QA**: [`docs/manual_review.md`](docs/manual_review.md)
- **Year Coverage Analysis**: [`output/reports/year_coverage.csv`](output/reports/year_coverage.csv)
- **QA Verification Report**: [`reports/manual_review_report.md`](reports/manual_review_report.md)
- **Sprint 1 Retrospective**: [`docs/sprint1_retrospective.md`](docs/sprint1_retrospective.md)
- **Exploratory SQL Queries**: [`notebooks/exploratory_queries.sql`](notebooks/exploratory_queries.sql)




