# Nifty 100 Financial Intelligence - System Architecture

This document details the architectural layout, component interactions, database schema, and object relationships for the Nifty 100 Financial Intelligence Platform.

## 1. System Overview

The platform uses a decoupled three-tier architecture:
- **Data Tier**: SQLite3 database (`db/nifty100.db`) storing company metadata, historical financials (P&L, Balance Sheet, Cash Flow), daily stock prices, and pre-calculated analytical ratios.
- **Service Tier (Backend)**: FastAPI REST API exposing standard endpoints for screening, peer group rankings, and dynamic valuation metrics.
- **Presentation Tier (Frontend)**: Modular Streamlit dashboard providing interactive charting, screens, tearsheets, and comparative reports.

```mermaid
graph TD
    User((Analyst User)) -->|Interacts| UI[Streamlit Frontend]
    UI -->|HTTP requests| API[FastAPI REST Backend]
    API -->|SQL queries| DB[(SQLite Database)]
    ETL[ETL Pipeline main.py] -->|Seeds/Updates| DB
    RawData[Excel Raw Data] -->|Parsed by| ETL
```

---

## 2. Database Schema (ER Diagram)

The database schema is optimized for range queries, sector aggregation, and fast financial ranking joins.

```mermaid
erDiagram
    COMPANIES ||--o| SECTORS : has_sector
    COMPANIES ||--o| ANALYSIS : has_analysis
    COMPANIES ||--o| PROSANDCONS : has_proscons
    COMPANIES ||--o| PROFITANDLOSS : has_pl
    COMPANIES ||--o| BALANCESHEET : has_balancesheet
    COMPANIES ||--o| CASHFLOW : has_cashflow
    COMPANIES ||--o| DOCUMENTS : has_documents
    COMPANIES ||--o| STOCK_PRICES : has_prices
    COMPANIES ||--o| PEER_GROUPS : has_peers
    COMPANIES ||--o| FINANCIAL_RATIOS : has_ratios
    COMPANIES ||--o| WATCHLISTS : bookmarked_by
    USERS ||--o| WATCHLISTS : owns

    COMPANIES {
        text id PK "Ticker Symbol e.g. TCS"
        text company_name
        text about_company
        real face_value
        real book_value
        real roce_percentage
        real roe_percentage
    }

    SECTORS {
        integer id PK
        text company_id FK
        text broad_sector
        text sub_sector
        real index_weight_pct
        text market_cap_category
    }

    FINANCIAL_RATIOS {
        integer id PK
        text company_id FK
        text year
        real net_profit_margin_pct
        real operating_profit_margin_pct
        real return_on_equity_pct
        real return_on_capital_employed_pct
        real return_on_assets_pct
        real debt_to_equity
        real interest_coverage
        real free_cash_flow_cr
        real composite_quality_score
    }

    PROFITANDLOSS {
        text company_id PK, FK
        text year PK
        real sales
        real operating_profit
        real net_profit
        real eps
    }
```

---

## 3. Sequence Diagram (User Request Flow)

This diagram describes the lifecycle of an analytical request (e.g. running the Screener or loading a Company profile):

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as Streamlit Dashboard
    participant Backend as FastAPI REST API
    participant DB as SQLite3 Database
    participant Analytics as Analytics Engines (Screener, Peer, Valuation)

    User->>Frontend: Clicks 'Run Preset: Value Pick'
    Frontend->>Backend: GET /screen?preset=Value+Pick
    Backend->>DB: Query constituent financial profiles
    DB-->>Backend: Return raw company records
    Backend->>Analytics: Run Screener Engine (load_screener_master_data & run_preset)
    Analytics-->>Backend: Return filtered & sorted DataFrame
    Backend-->>Frontend: HTTP 200 OK (JSON Data)
    Frontend-->>User: Render styled interactive Table & Chart
```

---

## 4. Class & Component Diagram

The code structure uses independent functional managers that import shared configurations and helper utils:

```mermaid
classDiagram
    class Settings {
        +Path BASE_DIR
        +Path DB_PATH
        +Path OUTPUT_DIR
    }

    class DatabaseManager {
        +get_connection(db_file)
        +get_db(db_file)
    }

    class RatioEngine {
        +compute_profitability_ratios(df_pl, df_bs)
        +compute_leverage_ratios(df_bs)
        +populate_ratios_db(db_path)
    }

    class ValuationEngine {
        +load_market_cap(filepath)
        +compute_valuation_metrics(df_mcap, df_master)
        +run_valuation_pipeline(db_path)
    }

    class ScreenerEngine {
        +load_screener_master_data(db_path)
        +run_preset(preset_name, df_master)
    }

    class PeerComparisonEngine {
        +run_peer_analysis(db_path)
        +calculate_sector_statistics(df)
    }

    RatioEngine ..> Settings : references
    ValuationEngine ..> Settings : references
    DatabaseManager <.. RatioEngine : connections
    DatabaseManager <.. ValuationEngine : connections
    DatabaseManager <.. ScreenerEngine : connections
    DatabaseManager <.. PeerComparisonEngine : connections
```
