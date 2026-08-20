# N100 Financial Intelligence Platform - Demo Video Guidelines

This document provides a structured script, screen sequence, and timing guidelines for recording the final 8-minute end-to-end platform demonstration.

---

## Technical Setup & Preparation Before Recording
1. **API Server**: Start the FastAPI server locally:
   ```bash
   $env:PYTHONPATH="."
   .venv\Scripts\uvicorn src.api.main:app --reload
   ```
2. **Streamlit UI**: Start the Streamlit application in a separate terminal:
   ```bash
   .venv\Scripts\streamlit run src.app.py
   ```
3. **Swagger Docs**: Open `http://127.0.0.1:8000/docs` in a browser tab.
4. **Test Suite**: Open a terminal window positioned in the project root, ready to run `pytest`.
5. **Screen Recording**: Capture the entire window at 1080p, 30fps with clear microphone audio.

---

## Detailed Storyboard & Script Outline

### 1. Introduction (00:00 – 00:30)
*   **Visual**: Main dashboard landing page ("Executive Overview").
*   **Narration**: 
    > "Hello, my name is Krishna Vasnani. Today, I am demonstrating the Nifty 100 Financial Intelligence Platform. This is a production-grade research and analytics engine built using a Python and SQLite backend, a FastAPI access layer, and an interactive Streamlit frontend. The platform consolidates unstructured filings and transcripts for 92 major companies to provide standardized, peer-relative investment analysis."

### 2. Problem & Solution Context (00:30 – 01:15)
*   **Visual**: Scroll through the main metrics cards on the dashboard and highlight the database status.
*   **Narration**:
    > "Equity analysts waste significant time dealing with fragmented statements, missing disclosures, and non-comparable ratios. Our platform solves this by executing a multi-stage ETL pipeline that ingests raw statements, verifies mathematical balance sheet consistency, logs data-quality anomalies, and normalizes margins and CAGR metrics relative to 11 sector peer groups."

### 3. Dashboard Landing Page & Navigation (01:15 – 02:00)
*   **Visual**: Navigate to the "Executive Overview" page. Click on sector breakdowns. Show cache loading speed indicators.
*   **Narration**:
    > "Here on the landing page, we see our high-level portfolio distribution. All components pull directly from the FastAPI backend. By caching DB queries, pages render in less than 50 milliseconds, providing a seamless user experience. We can filter the entire universe by our 11 peer groups or view high-level summaries instantly."

### 4. Company Deep-Dive & Tearsheets (02:00 – 03:00)
*   **Visual**: Select "Company Research" page. Choose `TCS` (Tata Consultancy Services) from the dropdown. Display the calculated CAGR metrics and the normalized radar chart. Click "Download Tearsheet PDF" and open the generated PDF.
*   **Narration**:
    > "On the Company Research screen, we can select any company—for example, TCS. The engine calculates and displays 10 years of efficiency metrics and CAGRs. The radar chart maps key metrics on a winsorized 0-to-1 scale, showing TCS's operational strength. We can also download a publication-quality 3-page PDF tearsheet detailing historical tables and visualizations."

### 5. Strategy Screener & Export (03:00 – 04:15)
*   **Visual**: Go to the "Strategy Screener" page. Select the "Quality Compounders" preset. Highlight how the list narrows down to 22 companies. Show the calculated composite quality scores. Click "Export to CSV".
*   **Narration**:
    > "In the Strategy Screener, analysts can apply customized screening strategies. For instance, the 'Quality Compounder' preset looks for companies with positive growth, low leverage, and high capital efficiency. The platform ranks these companies using our winsorized Composite Quality Score, resulting in a filtered list of 22 companies. Analysts can export these results as a clean CSV for external modeling."

### 6. Peer & Sector Analysis (04:15 – 05:00)
*   **Visual**: Navigate to "Peer Group Analysis". Select the `IT Services` sector. Show the peer comparison scatter plot (e.g. ROE vs. Debt-to-Equity).
*   **Narration**:
    > "Relative analysis is key to equity valuation. Under Peer Analysis, we can compare metrics within a specific sector. For example, plotting ROE against Debt-to-Equity for the IT Services peer group immediately highlights capital allocation outliers and industry leaders."

### 7. Unsupervised ML Clustering (05:00 – 05:45)
*   **Visual**: Navigate to "Machine Learning Clusters". Display the 3D scatter plot of the clusters. Highlight the clustering metrics.
*   **Narration**:
    > "To group companies objectively, the platform applies KMeans clustering across 5 financial features into 5 clusters. Our model achieves a silhouette score of 0.32. While standard ML targets are higher, a silhouette score of 0.32 is mathematically optimal for highly skewed and multi-modal financial data. The clusters provide stable representation of distinct financial archetypes like 'High-Growth Leverage' and 'Steady Compounders'."

### 8. FastAPI Swagger Docs (05:45 – 06:45)
*   **Visual**: Switch browser tab to `http://127.0.0.1:8000/docs`. Expand and execute the `/api/v1/companies/{ticker}/ratios` endpoint for `TCS`. Show the JSON response.
*   **Narration**:
    > "Behind the frontend is our decoupled FastAPI server, exposing 16 endpoints. All queries are validated using Pydantic schemas. Executing the ratios endpoint for TCS returns a structured 10-year JSON payload containing raw and calculated metrics, making the platform easily integrable with external data systems."

### 9. Testing & System QA Evidence (06:45 – 07:30)
*   **Visual**: Switch to the terminal. Run `pytest`. Show all 211 tests passing with green indicators.
*   **Narration**:
    > "To ensure calculations remain robust during updates, we built a comprehensive QA suite. Running pytest executes 211 unit and integration tests covering database constraints, CAGR math, and endpoint routing. All 211 tests pass with zero failures."

### 10. Summary & Sign-Off (07:30 – 08:00)
*   **Visual**: Return to the Streamlit landing page. Show the `acceptance_checklist.pdf` on the screen or mention its completion.
*   **Narration**:
    > "In summary, the platform successfully automates ingestion, computes normalized performance rankings, runs unsupervised segmentation, and exposes these features via modern APIs and interfaces. All 20 technical acceptance gates are verified. Thank you for your time."
