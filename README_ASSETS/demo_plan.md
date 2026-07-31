# N100 Repository Presentation — 90-Second Demo Plan

This script is structured for a 60–90 second recorded walkthrough of the N100 Financial Intelligence Platform, optimized for recruiters and systems engineers.

---

## ⏱️ Video Script Timeline

### 0:00 - 0:15 | The Problem & Value Proposition (The Hook)
*   **Visual**: Screen showing the repository README with the professional hero banner.
*   **Audio (Voiceover)**: 
    > "Financial analysts are often buried under inconsistent company filings and error-prone Excel tables, where a single incorrect balance sheet cell can break valuation models. 
    > To solve this, I engineered N100—a production-grade Financial Intelligence Platform that automates Excel data ingestion, validates inputs against a strict 16-rule data quality engine, and processes composite scores in a relational SQLite store."

### 0:15 - 0:40 | System Architecture & ETL Flow (The Design)
*   **Visual**: Scroll down README to highlight the System Architecture and ETL Flow SVG diagrams. Hover over the validation stages.
*   **Audio (Voiceover)**:
    > "Here is the request and data lifecycle. The ETL pipeline standardizes tickers and filing periods before running them through five blocker and eleven warning checks. 
    > If a critical check fails—such as assets not equaling liabilities—the system issues a complete database rollback, guaranteeing transactional integrity. Clean records are stored in a WAL-mode SQLite database with composite indexing."

### 0:40 - 1:10 | Execution Demo (The Evidence)
*   **Visual**: Switch to a split screen showing terminal output on the left and the Streamlit dashboard on the right. Run `run.bat` in the terminal to show the pipeline running in real-time.
*   **Audio (Voiceover)**:
    > "Running our automated execution helper script triggers the ingestion. The pipeline reads the filings, validates thousands of cells, and updates the database.
    > Immediately, the web terminal dashboard updates. Using custom cached queries, it renders sector asset distributions and composite quality metrics. Ratios like sector-relative ROE and FCF Yield are calculated instantly."

### 1:10 - 1:30 | Reliability & Results (The Wrap-Up)
*   **Visual**: Switch back to terminal and run `test.bat` showing all 279 tests passing green. Close on the contributing guide.
*   **Audio (Voiceover)**:
    > "The entire system is backed by a 279-test Pytest suite, covering validation rules, query managers, and math logic, guaranteeing zero regression. 
    > The repository features automated setup scripts and contributor guides, allowing any new developer to be onboarded in minutes. Thanks for watching."
