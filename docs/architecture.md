# System Architecture Specification

This document provides a detailed overview of the system architecture, component responsibilities, request lifecycle, data lifecycle, and system boundaries for the **Nifty 100 Financial Intelligence Platform**.

---

## 1. High-Level System Overview

The platform uses a decoupled, local-first architecture to ingest raw corporate financial reports, validate data quality, load standard structures into a relational database, compute financial KPIs, and display insights via a responsive web terminal dashboard.

![System Architecture Map](../README_ASSETS/architecture.svg)

### 📐 Text-Based Architecture Diagram
```text
 +-------------------------------------------------------------------------+
 |                          1. INGESTION LAYER                             |
 |  [Raw Excel Files] ---> (ExcelLoader) ---> (String/Date Normalizers)    |
 +---------------------------------------------------------|---------------+
                                                           v
 +-------------------------------------------------------------------------+
 |                          2. VALIDATION ENGINE                           |
 |               (DataValidator runs 16 Data Quality Rules)                |
 |               /                                         \               |
 |              v (Fail 5 Blocker Rules)                    v (Pass)       |
 |    [Detailed Rejection CSVs]                   [Clean DataFrames]       |
 +---------------------------------------------------------|---------------+
                                                           v
 +-------------------------------------------------------------------------+
 |                          3. RELATIONAL DATABASE                         |
 |           SQLite Store (ACID Transactions, Foreign Key Enforcements)   |
 |           Automatic Snapshot Backups <---> WAL Read/Write Journals     |
 +---------------------------------------------------------|---------------+
                                                           v
 +-------------------------------------------------------------------------+
 |                         4. CALCULATION ENGINES                          |
 |  [Ratios Engine]  ---> Computes Margins, ROE, ROCE, interest coverage   |
 |  [CAGR Engine]    ---> Computes 3Y/5Y/10Y rolling growth with math guard |
 |  [Cash Flow Engine]--> Classifies 8 Capital Allocation archetypes       |
 |  [Valuation Engine]--> Computes relative PE ranks & FCF Yield           |
 +---------------------------------------------------------|---------------+
                                                           v
 +-------------------------------------------------------------------------+
 |                         5. PRESENTATION LAYER                           |
 |  Streamlit Dashboard UI <---> Plotly Charts <---> ReportLab PDF Generator|
 +-------------------------------------------------------------------------+
```

---

## 2. Component Responsibilities

| Component | Namespace / Path | Responsibilities |
| :--- | :--- | :--- |
| **Ingestion Engine** | `src.etl.loader` | Parses multiple Excel spreadsheets, auto-detects row/column offsets, cleans headers, standardizes tickers, and normalizes dates. |
| **Data Quality Suite** | `src.validation.validator` | Executes 16 rule modules, segregating failures into critical blockers and non-blocking warnings, and writes diagnostic reports to `output/validation/`. |
| **Database Manager** | `src.database` | Creates database tables using schemas, handles bulk transactional insertions, rotates backups under `db/backups/`, and runs relational validation checks (FK constraints). |
| **Analytics Core** | `src.analytics` | Evaluates financial metrics, runs growth trend CAGRs with sign-suppressors, classifies capital spending patterns, and populates the database `financial_ratios` table. |
| **Visualizer & UI** | `app.py`, `src.dashboard` | Implements glassmorphism UI pages, builds interactive charts (radar, treemap, scatter), handles session logins, and compiles PDF reports. |

---

## 3. Data Lifecycle

The lifecycle of data through the platform consists of six distinct stages:

```text
  [Input]        [Normalize]       [Validate]       [Persist]        [Compute]        [Present]
Raw Excel  ===> Strip Spaces ===> Check DQ-01 ===> SQLite Transaction ===> Run Ratios ===> Streamlit UI
Filings         Format Dates      to DQ-16        Commit/Rollback  Populate DB      Plotly Charts
```

1.  **Ingestion (Raw Input)**: Raw Excel filing files are dropped into `data/raw/`. The pipeline reads the files, detecting offsets.
2.  **Normalization (Structuring)**: Tickers are standardized to uppercase characters (e.g., `TCS.NS` to `TCS`) and dates are normalized to calendar month formats (`YYYY-MM`).
3.  **Data Quality Validation (Gatekeeping)**: The `DataValidator` checks the normalization results against 16 rules. If a blocker rule fails, the pipeline halts database insertion and logs details to `output/validation/validation_failures.csv`.
4.  **Persistence (Transactional Load)**: Data passing validation checks is written to the SQLite database. The entire load is executed inside a single transaction; any failure during write triggers a complete database rollback.
5.  **Analytics & Computation (KPI Population)**: Modulators read SQLite raw financial tables (`profitandloss`, `balancesheet`, `cashflow`), execute formulas, and write the computed results directly back to the database `financial_ratios` table.
6.  **Presentation (Visualization)**: Streamlit reads from the database `financial_ratios` and master tables, rendering interactive Plotly charts and compiling PDF documents on demand.

---

## 4. Request Lifecycle

When a user interacts with the dashboard interface:
1.  **Session Initializer**: Streamlit loads and verifies user login credentials against the `users` SQLite table (`hashlib.sha256` hash comparison).
2.  **Cache Verification**: The dashboard checks Streamlit's `@st.cache_data` memory. If the query parameters (e.g., selected sector or company) match, it loads the data from RAM; otherwise, it hits the database.
3.  **Query & Join**: The database manager runs queries matching the request, joining tables (e.g. `companies` joined with `financial_ratios` and `sectors`) using optimized indexes.
4.  **UI Render**: DataFrames are processed into Plotly graphs and markdown elements, displaying the update in under 1.2 seconds.

---

## 5. System Boundaries

*   **Offline Operation**: The platform is 100% self-contained. It performs zero external HTTP requests to scrape data or verify security during run execution, ensuring speed and absolute reliability.
*   **Single-Host Storage**: Relies on a local file-based database. It does not support network connections from remote database clients.
*   **Template Dependent Ingest**: Raw filings must conform to standard Indian exchange reporting formats. If raw schema columns are significantly altered, new parsing patterns must be added to `loader.py`.
