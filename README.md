# Nifty 100 Financial Intelligence Platform

<div align="center">

![Platform Banner](README_ASSETS/banner.png)

### Production-Grade Financial Data Engineering & KPI Analytics Platform for the Indian Equity Market

**An end-to-end, institutional-grade analytics pipeline that automates raw financial filing ingestion, enforces 16 strict data validation rules, populates a relational database, and generates visual equity research insights.**

---

🚀 [Live Demo (Placeholder)](#) • 📖 [System Design Specification](docs/system_design.md) • 🖥️ [Dashboard Preview](#-dashboard-preview) • 📹 [Demo Video (Placeholder)](#)

---

[![Python 3.14+](https://img.shields.io/badge/Python-3.14%2B-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite 3](https://img.shields.io/badge/SQLite-3-003B57.svg?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75.svg?style=flat-square&logo=plotly&logoColor=white)](https://plotly.com/)
[![pytest](https://img.shields.io/badge/Tests-234%20Passed-2EA44F.svg?style=flat-square&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

</div>

---

### 📊 Repository Statistics

| 🏢 Companies | 📈 Financial KPIs | 🖥️ Dashboard Screens | 🧪 Test Suite | 🛡️ DQ Rules | ⚡ App Latency |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **92** | **50+** | **8 Independent Pages** | **234 Tests (100% Pass)** | **16 Ingestion Checks** | **< 2.5 Seconds** |

---

### 🛠️ Technology Stack

| Category | Technologies |
| :--- | :--- |
| **Backend & Storage** | Python, SQLite |
| **Data Processing** | Pandas, NumPy, OpenPyXL |
| **Dashboard UI** | Streamlit, Plotly |
| **Testing** | Pytest |
| **VCS & DevOps** | Git, GitHub |

---

## 🎯 About the Project

### 💡 Why this project?
Professional financial terminals like Bloomberg and Reuters charge tens of thousands of dollars, while retail services like Screener.in and Tickertape keep their analytical engines closed-source. This project recreates the entire underlying infrastructure from scratch, showcasing clean data engineering, strict quality control, custom metrics calculations, and premium visualizations.

### ⚠️ The Problem
Raw financial data in the Indian equity markets (specifically Nifty 100 constituents) is highly fragmented. File structures shift between years, tickers are un-normalized, date formats vary, and arithmetic inconsistencies (e.g. mismatched balance sheets or misreported tax rates) corrupt downstream analytics.

### 🛠️ The Solution
A robust, multi-stage ETL pipeline that ingests raw excel filings, runs 16 data quality checks, normalizes data structures into a clean relational database, and exposes calculations through a responsive, multi-page analytical dashboard.

---

## 🚀 Key Highlights

*   **12-Source Ingestion Pipeline**: Auto-detects row/column offsets, stripping white spaces and standardizing ticker names.
*   **16-Rule Data Quality Suite**: Segregates errors into critical blockers (blocking db writes) and warning anomalies.
*   **ACID-Compliant Relational DB**: SQLite engine enforcing referential integrity with cascade deletes and automated load backups.
*   **Flexible Growth & Ratio Engines**: Custom math helpers (`safe_divide`) handling 6 edge cases of CAGR calculation (e.g., turnaround or negative bases) and 8 distinct Capital Allocation Patterns.
*   **Interactive Multi-Page Dashboard**: A Streamlit interface powered by custom-themed Plotly charts.

---

## ⚙️ Project Workflow

```text
Raw Excel Ingest ➔ Data Quality Rules ➔ SQLite DB Ingest ➔ KPI Analytics Engines ➔ Streamlit Dashboard ➔ CSV & PDF Reports
```

---

## 🖥️ Dashboard Preview

The frontend is broken down into **8 comprehensive, independent pages** allowing granular research:

| 🏠 01 Executive Home | 👤 02 Company Profile |
| :---: | :---: |
| ![Home](README_ASSETS/01_home.png) | ![Profile](README_ASSETS/02_profile.png) |
| 🔍 03 Investment Screener | 📊 04 Peer Comparison |
| ![Screener](README_ASSETS/03_screener.png) | ![Peers](README_ASSETS/04_peers.png) |
| 📈 05 Trend Analysis | 🏭 06 Sector Analytics |
| ![Trends](README_ASSETS/05_trends.png) | ![Sector](README_ASSETS/06_sectors.png) |
| 💰 07 Capital Allocation Map | 📄 08 Reports Browser |
| ![Capital](README_ASSETS/07_capital.png) | ![Reports](README_ASSETS/08_reports.png) |

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Raw Ingestion Layer
        A[12 Excel Files / raw data] -->|Inbound Parser| B[ExcelLoader Engine]
        B -->|Date & Ticker Standardizer| C[String Normalization]
    end

    subgraph Data Quality Suite
        C --> D{16 DQ Rules Evaluator}
        D -->|5 Critical Blockers| E[Rejection / Failure CSV Logs]
        D -->|11 Non-Blockers| F[Anomalies Log / Continue Load]
    end

    subgraph Relational Database
        F -->|Transactional Load| G[(SQLite Relational DB)]
        G -->|PRAGMA foreign_keys = ON| G
        G -->|Auto-Backup Handler| H[(db/backups/)]
    end

    subgraph Analytical Engines
        G --> I[Profitability & Solvency Engine]
        G --> J[10-Year CAGR Growth Engine]
        G --> K[Cash Flow & Capital Allocation Engine]
        I -->|Export Ratios| L[ratio_calculation_log.csv]
        J -->|Export CAGR| M[growth_summary.csv]
        K -->|Export Allocation| N[capital_allocation.csv]
    end

    subgraph Multi-Page Dashboard
        G --> O[Streamlit Dashboard Web App]
        L --> O
        M --> O
        N --> O
        O -->|01| O1[Executive Home]
        O -->|02| O2[Company Profile]
        O -->|03| O3[Investment Screener]
        O -->|04| O4[Peer Comparison]
        O -->|05| O5[Trend Analysis]
        O -->|06| O6[Sector Analytics]
        O -->|07| O7[Capital Allocation]
        O -->|08| O8[Annual Reports]
    end

    style A fill:#2d3748,stroke:#4a5568,stroke-width:1px,color:#fff
    style G fill:#1a365d,stroke:#2b6cb0,stroke-width:2px,color:#fff
    style O fill:#2c5282,stroke:#4299e1,stroke-width:2px,color:#fff
    style D fill:#744210,stroke:#d69e2e,stroke-width:1px,color:#fff
```

---

## ⚡ Performance Benchmarks

| Benchmark Metric | Measurement |
| :--- | :--- |
| Full ETL Pipeline Ingestion | < 8.0 Seconds |
| Database Seed & Build time | < 5.0 Seconds |
| Dashboard Page Load Latency | < 2.5 Seconds |
| SQL Query Response Time | < 0.1 Seconds |
| Test Suite Execution (234 Tests) | < 12.0 Seconds |

---

## 🛠️ Quick Start

```bash
# 1. Clone & Navigate
git clone https://github.com/krishnavasnani07/n100-financial-intelligence-platform.git
cd n100-financial-intelligence-platform

# 2. Setup environment
python -m venv venv

# 3. Install packages
pip install -r requirements.txt

# 4. Build database & calculate KPIs
python main.py

# 5. Launch interactive web dashboard
streamlit run src/dashboard/app.py
```

<details>
<summary>🔑 Platform-Specific Environment Activation details</summary>

Activate on Windows (Command Prompt):
```cmd
venv\Scripts\activate.bat
```
Activate on Windows (PowerShell):
```powershell
venv\Scripts\Activate.ps1
```
Activate on Linux/macOS:
```bash
source venv/bin/activate
```

</details>

---

## 🧪 Testing & Engineering Quality

A comprehensive test suite containing **234 automated tests** covers database integrity, business logic validation, edge cases, and arithmetic operations:

```bash
python -m pytest tests/ -v
```

---

## 🗺️ Sprint Roadmap

```text
Sprint 1 : Ingestion, Validation & Database Load   [████████████████████] 100% (Completed)
Sprint 2 : Financial KPI Engines & CAGR Analysis   [████████████████████] 100% (Completed)
Sprint 3 : Visualization Engine & CSV Bulk Export   [████████████████████] 100% (Completed)
Sprint 4 : Streamlit Interactive Dashboards        [████████████████████] 100% (Completed)
Sprint 5 : Watchlists, Alerts & REST API Layer     [░░░░░░░░░░░░░░░░░░░░]   0% (Backlog)
```

---

<details>
<summary>📂 Repository Structure Details</summary>

```text
n100-financial-intelligence-platform/
├── README_ASSETS/           # Custom banner, diagrams, and preview screenshots
├── data/                    # Ingestion stages (raw, processed, external)
├── db/                      # Schema DDL, SQLite DB, and automated backups
├── docs/                    # Architectural & domain design guides
├── logs/                    # Operational logging
├── notebooks/               # EDA & SQL prototyping scripts
├── output/                  # Analytics outputs and database audit tables
├── src/                     # Core application source code
│   ├── analytics/           # KPI, CAGR, and Cash Flow engines
│   ├── config/              # Central configurations (ratios, CAGR, cashflow)
│   ├── database/            # SQLite connector & table loaders
│   ├── etl/                 # Excel Ingestion and normalization pipeline
│   ├── utils/               # App logging & helper utilities
│   ├── validation/          # 16 Data Quality rules framework
│   └── dashboard/           # Streamlit app logic & modular components
│       ├── app.py           # Dashboard routing & navigation entrypoint
│       ├── assets/          # CSS stylesheets and brand logos
│       ├── components/      # Reusable UI charts, tables, & filters
│       ├── pages/           # 8 analytical dashboard screens
│       └── utils/           # Shared database query connections
├── tests/                   # 234 automated pytest suites
├── main.py                  # CLI pipeline runner
├── requirements.txt         # Package dependencies
└── README.md                # Project documentation
```

</details>

<details>
<summary>📐 Technical Details & KPI Formulations</summary>

### 1. Profitability & Solvency Ratios
- **Net Profit Margin (NPM)**:
  $$\text{NPM} = \frac{\text{Net Profit}}{\text{Sales Revenue}} \times 100$$
  *Benchmarking*: Excellent ($\ge 15\%$), Good ($\ge 10\%$), Average ($\ge 5\%$), Weak ($< 5\%$).
- **Return on Equity (ROE)**:
  $$\text{ROE} = \frac{\text{Net Profit}}{\text{Equity Capital} + \text{Reserves}} \times 100$$
  *Edge Case*: Assigns `None` with `NON_POSITIVE_EQUITY` status if equity $\le 0$ to avoid false division anomalies.
- **Return on Capital Employed (ROCE)**:
  $$\text{ROCE} = \frac{\text{EBIT}}{\text{Equity Capital} + \text{Reserves} + \text{Borrowings}} \times 100$$
- **Debt-to-Equity (D/E)**:
  $$\text{D/E} = \frac{\text{Borrowings}}{\text{Equity Capital} + \text{Reserves}}$$
- **Interest Coverage Ratio (ICR)**:
  $$\text{ICR} = \frac{\text{Operating Profit} + \text{Other Income}}{\text{Interest Expense}}$$

### 2. Growth & Cash Flow Analytics
- **Compound Annual Growth Rate (CAGR)**:
  $$\text{CAGR} = \left[\left(\frac{\text{End Value}}{\text{Start Value}}\right)^{\frac{1}{\text{Years}}} - 1\right] \times 100$$
- **Free Cash Flow (FCF)**:
  $$\text{FCF} = \text{CFO} + \text{CFI}$$
- **CFO Quality Score**:
  $$\text{CFO Quality} = \frac{\text{CFO}}{\text{PAT}}$$
- **Capital Allocation Patterns**: Evaluates net direction $(\text{CFO}, \text{CFI}, \text{CFF})$ signs to identify corporate strategies (Reinvestor, Liquidator, Cash Accumulator, Distress Signal, etc.).

</details>

<details>
<summary>🛡️ Ingest Validation (16 DQ Rules)</summary>

#### Blocker Rules (Ingestion Stops on Failure)
- **DQ-01**: Primary Key Uniqueness on companies.
- **DQ-02**: Composite Uniqueness on `(company_id, year)`.
- **DQ-03**: Foreign Key referential integrity.
- **DQ-07**: Date formatting (`YYYY-MM` check).
- **DQ-08**: Ticker format validation.

#### Warning Rules (Load Continues, Log Warns)
- **DQ-04**: Balance Sheet balances (`Total Assets == Total Liabilities`).
- **DQ-05**: Calculated vs. Reported Operating Margins check.
- **DQ-06**: Positive sales validation.
- **DQ-09**: Net cash flow sum checksum.
- **DQ-10**: Fixed Assets boundary check.
- **DQ-11**: Tax rate limits ($[0\%, 100\%]$).
- **DQ-12**: Dividend payout bounds.
- **DQ-13**: Web page URL validations.
- **DQ-14**: Net profit and EPS sign alignment.
- **DQ-15**: Balance Sheet sub-category validations.
- **DQ-16**: Historical record length threshold ($>5$ years).

</details>

---

## 🎓 Skills Demonstrated & Resume Alignment

- **Data Engineering**: Multi-stage ETL, schema validation, ACID compliance, relational database design, transaction handling, and auto-backups.
- **Financial Analytics**: Implementation of complex equity research calculations (profitability, leverage, multi-period CAGR engines, and cash flow strategies).
- **Frontend & Visualization**: Multi-page web dashboard routing, Plotly interactive graphics (polar plots, treemaps, bubble charts).
- **Software Engineering**: Pytest suite automation, clean code structuring, configuration separations, and error boundary handling.

---

## 🤝 Acknowledgements

- **Bluestock Fintech** for project requirements and datasets.
- **Screener.in** and **Tickertape** for functional inspiration.
- Open source libraries: **Streamlit**, **Plotly**, and **Pandas**.

---

## 👤 About the Developer

**Krishna Vasnani** - Bluestock Fintech Analytics Intern

- **GitHub**: [@krishnavasnani07](https://github.com/krishnavasnani07)
- **LinkedIn**: [Krishna Vasnani](https://linkedin.com/in/krishnavasnani07)
- **Email**: krishnavasnani07@gmail.com
- **Project**: Nifty 100 Financial Intelligence Platform

---

<div align="center">

MIT License • Made with ❤️ using Python and Streamlit

</div>
