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

