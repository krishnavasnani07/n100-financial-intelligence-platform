# Architectural Design Decisions & Trade-Offs

This document captures the critical design decisions made during the development of the **Nifty 100 Financial Intelligence Platform**, documenting the problems, alternatives, chosen solutions, and engineering trade-offs.

---

## 1. Relational SQLite Backend vs. NoSQL Document Stores

### Problem
Financial data (companies, yearly Profit & Loss, Balance Sheet statements, and computed analytical ratios) is highly structured and interconnected. A loose schema or document-oriented store makes calculating multi-period metrics (like CAGR or ROE trends) fragile and error-prone.

### Alternatives Considered
*   **MongoDB (NoSQL)**: High flexibility, but lacks referential integrity and is prone to data corruption if sheets alter schemas.
*   **PostgreSQL**: Strong ACID compliance and concurrency, but requires local setup, credentials management, and network connections, violating the zero-dependency onboarding goal.
*   **Flat CSV Files**: Simple, but lacks relational integrity, query joining capability, and query optimization via indexes.

### Chosen Solution
*   **SQLite3** with index optimization and explicit foreign key cascades (`PRAGMA foreign_keys = ON;`).

### Why?
Guarantees relational ACID database transactions and referential integrity (e.g. deleting a company deletes its ratios automatically) while enabling a clone-and-run local setup with zero credentials or connection configuration.

### Trade-Offs
*   *Limitation*: SQLite does not support distributed database scaling or high write-concurrency.
*   *Justification*: The ETL pipeline executes as a single-writer script locally on raw files, making write concurrency a non-issue.

---

## 2. Upfront Python Validation vs. Database Constraints

### Problem
Invalid filing values (such as text year values or mismatched balance sheets) cause SQL constraints to crash halfway through database loads, leaving the database in a partially loaded, corrupted state.

### Alternatives Considered
*   **Raw Database Constraint Validation**: Run verification using SQL constraints (`CHECK` parameters). This yields generic error strings (e.g. `CHECK constraint failed`) that are difficult to trace back to Excel coordinates.
*   **Post-Load SQL Scripts**: Load raw data directly to database and run validation checks afterwards. This exposes downstream dashboards to corrupt intermediate states.

### Chosen Solution
*   A dedicated Python `DataValidator` engine (`src/validation/validator.py`) executing 16 rules on Pandas DataFrames before database insertion.

### Why?
Detects errors upfront and generates a detailed audit CSV (`validation_failures.csv`) pointing directly to raw Excel sheets, columns, and rows, while protecting SQLite tables from corrupt writes.

### Trade-Offs
*   *Limitation*: Increases memory usage by loading all DataFrames into memory.
*   *Justification*: The total Nifty 100 historical dataset size is relatively small (under 100MB), making memory overhead negligible on modern development machines.

---

## 3. SQLite Journaling Mode: Write-Ahead Logging (WAL)

### Problem
The Streamlit application running on multiple browser tabs reads database tables continuously. A simultaneous write execution from the ETL pipeline (`main.py`) locks the database file, causing "Database is locked" errors on user screens.

### Alternatives Considered
*   **Default Journaling Mode (Rollback Journal)**: Locks the entire database file during writes, blocking concurrent readers.
*   **Thread Locks in Python Code**: Restricts concurrent DB reads via global software locks. This slows down dashboard rendering during database queries.

### Chosen Solution
*   **Write-Ahead Logging (WAL)**: Enabled via `PRAGMA journal_mode = WAL;`.

### Why?
Decouples readers and writers. Writing is appended to a separate log file (`.db-wal`), permitting concurrent dashboard reads without locks or database latency.

### Trade-Offs
*   *Limitation*: Creates extra temporary database files (`.db-wal` and `.db-shm`) and increases disk write wear.
*   *Justification*: SQLite manages these files automatically, and disk writes are minimal during daily/weekly filing loads.

---

## 4. CAGR Growth Math Guard

### Problem
Standard CAGR formulas (`(End / Start) ^ (1 / n) - 1`) fail or generate mathematically invalid positive percentages for volatile turnaround companies (e.g. shifting from a net loss to a net profit).

### Alternatives Considered
*   **Native NaN/Complex Returns**: Allow the division of negative bases to fail naturally or return complex numbers. This crashes downstream charts and dashboard elements.
*   **Flat Trend Averages**: Substitute CAGR with standard linear trend line growth. This misrepresents compound growth metrics to the analyst.

### Chosen Solution
*   An explicit CAGR engine handling 6 financial edge cases (e.g. turnaround years where base was negative) by returning `None` and assigning categorical labels (`TURNAROUND`, `DECLINE_TO_LOSS`, etc.) instead of mathematically incorrect percentages.

### Why?
Prevents presenting misleading positive growth statistics for historically loss-making companies to recruiters and analysts.

### Trade-Offs
*   *Limitation*: Suppresses lines on trend charts for volatile businesses.
*   *Justification*: The suppression accurately reflects the mathematical reality, and labels notify users why the calculation is not applicable.
