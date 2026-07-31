# ETL & Data Ingestion Pipeline Specification

This document details the design and flow of the Extraction, Transformation, and Ingestion (ETL) pipeline, the Data Quality validation suite, and the database loading mechanisms for the **Nifty 100 Financial Intelligence Platform**.

---

## 1. Pipeline Execution Flow

The pipeline executes sequentially inside a single script run (`main.py`):

![ETL Data Ingestion Flow](../README_ASSETS/etl_flow.svg)

```text
 [Raw Input]        [Normalize]         [Validate]        [Database Load]      [Ratios Compute]
Read Excel file  ==> Standardize Ticker ==> Run 16 DQ  ==> SQLite Transaction ==> Compute KPIs
Detect Offsets       Standardize Year       Rules          Commit/Rollback        Populate DB
```

---

## 2. Ingestion & Normalization Details

### 2.1 File Parser (`src/etl/loader.py`)
Corporate financial reports are ingested from raw multi-tab Microsoft Excel worksheets. The ingestion engine:
*   **Auto-detects offsets**: Strips empty header rows and blank columns to locate the start of tables.
*   **Cleans Headers**: Strips whitespace and normalizes column text to clean uppercase letters.

### 2.2 String & Date Normalizers
*   **Ticker Normalizer (`normalize_ticker`)**: Converts corporate names or messy tickers (e.g. `Tcs`, `TCS.NS`, `TCS_EQ`) into standard uppercase short codes (`TCS`).
*   **Date Normalizer (`normalize_year`)**: Converts varying filing date strings (e.g., `31-Mar-24`, `2024-03`, `Mar-24`, `March 2024`) into a standard financial calendar period format (`YYYY-MM`).

---

## 3. Data Quality (DQ) Validation Framework

Before any record is written to SQLite, dataframes are evaluated by the `DataValidator` engine against 16 rules.

### 📐 Text-Based Validation Flow
```text
                  [Normalized DataFrame Input]
                                │
                                ▼
                   ┌─────────────────────────┐
                   │  16 DQ Rules Evaluator  │
                   └────────────┬────────────┘
                                │
             ┌──────────────────┴──────────────────┐
             ▼                                     ▼
     [5 Blocker Rules]                     [11 Warning Rules]
     (Fails DQ-01,02,03,07,08)             (Fails DQ-04,05,06,09..16)
             │                                     │
             ▼                                     ▼
┌─────────────────────────┐               ┌─────────────────────────┐
│ Log Critical Failure    │               │ Log Warning Anomaly     │
│ Suppress Ingestion      │               │ Allow Data to Proceed   │
│ Generate Rejection CSV  │               │ Write Warning Log       │
└─────────────────────────┘               └─────────────────────────┘
```

### 3.1 Blocker Rules (5 Checks)
Critical violations that threaten relational database integrity. If any check fails, the pipeline halts database insertion:
1.  **`DQ-01` (Company Key Unique)**: Verifies that company master tickers are unique.
2.  **`DQ-02` (Filing Period Unique)**: Verifies that only one filing period `(company_id, year)` exists.
3.  **`DQ-03` (Foreign Key Validity)**: Confirms company keys exist in master tables.
4.  **`DQ-07` (Year Format Standard)**: Enforces calendar formatting (`YYYY-MM`) and rejects un-standardized values (e.g. `TTM`).
5.  **`DQ-08` (Ticker Length/Format)**: Enforces uppercase alphanumeric codes.

### 3.2 Warning Rules (11 Checks)
Financial arithmetic and data anomalies. If these fail, warnings are logged, but the load continues:
1.  **`DQ-04` (Balance Sheet Equilibrium)**: Asserts that $Assets == Liabilities$.
2.  **`DQ-05` (Operating Margin Cross-Check)**: Verifies that computed OPM matches reported OPM (tolerance $\le 1.0\%$).
3.  **`DQ-06` (Positive Revenue)**: Flags companies reporting negative revenue.
4.  **`DQ-09` (Net Cash Flow Summation)**: Confirms Cash Flow statements sum to the reported total ($CFO + CFI + CFF == NCF$).
5.  **`DQ-10` to `DQ-16`**: Reinvestments, tax rates (within $0\% - 45\%$), dividend payouts, and missing URL links checks.

---

## 4. Loading & Transaction Management

Data passing validation checks is loaded into SQLite:
1.  **Database Connection Context**: Employs Python context managers (`sqlite3.connect`) ensuring connections close cleanly.
2.  **ACID Transactions**: Executes imports inside transaction frames. If loading fails (e.g. key collision or database lock), `conn.rollback()` executes, returning the database to its pre-ETL state.
3.  **Referential Constraints**: Verifies `PRAGMA foreign_keys = ON;` upon connection to prevent orphans.

---

## 5. Logging, Diagnostics, and Recovery

*   **Pipeline Run Output**: Running the pipeline outputs execution statistics in a clean text terminal dashboard layout:
    
    ![ETL Pipeline Execution CLI](../README_ASSETS/cli_execution.png)

*   **Failure Log Outputs**: Validation errors write diagnostic reports directly to `output/validation/validation_failures.csv` detailing the failed row, rule ID, and value.
*   **Pipeline Run Logs**: Log details (errors, statistics, counts) are appended to `logs/app.log` via standard Python logging.
*   **Recovery Backups**: The ETL process creates database copies inside `db/backups/` before starting, maintaining the last 5 backups.
