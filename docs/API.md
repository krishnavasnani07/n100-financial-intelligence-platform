# REST API Route Documentation

This document describes the API endpoints exposed by the Nifty 100 Financial REST API server.

## 1. Base URL & Interactive Docs

- **Local Base URL**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **Alternative ReDoc UI**: `http://localhost:8000/redoc`

---

## 2. API Endpoint Catalog

### 1. `GET /companies`
Lists all active companies in the platform database.
- **Parameters**: None
- **Response**: List of objects:
  ```json
  [
    {
      "id": "TCS",
      "company_name": "Tata Consultancy Services Ltd.",
      "broad_sector": "Information Technology",
      "sub_sector": "IT Services"
    }
  ]
  ```

---

### 2. `GET /company/{ticker}`
Retrieves details, metadata, and latest financial ratios for a given company.
- **Parameters**:
  - `ticker` (string, path parameter): The unique symbol (e.g. `INFY`, case-insensitive).
- **Response**:
  ```json
  {
    "company_id": "INFY",
    "company_name": "Infosys Limited",
    "broad_sector": "Information Technology",
    "sub_sector": "IT Services",
    "market_cap_category": "Large Cap",
    "return_on_equity_pct": 28.5,
    "debt_to_equity": 0.05,
    "free_cash_flow_cr": 21300.0,
    "composite_quality_score": 82.4
  }
  ```

---

### 3. `GET /valuation`
Calculates and returns valuation metrics (FCF Yield, median sector comparisons, and status flags) for the entire universe.
- **Parameters**: None
- **Response**:
  ```json
  [
    {
      "company_id": "TCS",
      "company_name": "Tata Consultancy Services Ltd.",
      "sector": "Information Technology",
      "PE": 28.4,
      "sector_median_pe": 26.1,
      "PE_vs_sector_median_pct": 108.8,
      "FCF_yield_pct": 3.9,
      "flag": "Fair"
    }
  ]
  ```

---

### 4. `GET /screen`
Filters companies using preset investment screeners.
- **Parameters**:
  - `preset` (string, query parameter, optional): The name of the preset strategy.
- **Available Presets**:
  - `Quality Compounder`
  - `Value Pick`
  - `Growth Accelerator`
  - `Dividend Champion`
  - `Debt-Free Blue Chip`
  - `Turnaround Watch`
- **Response** (if `preset` omitted):
  ```json
  {
    "available_presets": ["Quality Compounder", "Value Pick", ...],
    "message": "Use ?preset=<name> to screen companies."
  }
  ```
- **Response** (if `preset` provided): List of matching company profiles.

---

### 5. `GET /sector`
Provides sector metrics and aggregated stats.
- **Parameters**:
  - `name` (string, query parameter, optional): Specific broad sector to query.
- **Response** (if `name` omitted): Summary of all sectors.
- **Response** (if `name` provided): Detailed list of constituents and sector average indicators.

---

### 6. `GET /peer`
Generates peer benchmarking dashboards.
- **Parameters**:
  - `sector` (string, query parameter, optional): Specific sector.
- **Response**:
  ```json
  {
    "peer_comparison": [...],
    "top_performers": [...],
    "bottom_performers": [...],
    "sector_statistics": [...]
  }
  ```
