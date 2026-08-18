# Performance & Integration Test Notes

This document summarizes the performance benchmarks, load-testing, and database integration checks performed for Sprint 6 — Day 43.

## 1. Screener Load Test

* **Endpoint**: `GET /api/v1/screener`
* **Query Parameters**: `?min_roe=15`
* **Concurrency**: 10 concurrent requests using `ThreadPoolExecutor`
* **Successful requests**: 10
* **Failed requests**: 0
* **Total batch execution time**: 0.323 sec (target < 10.0 sec)
* **Average response time**: 0.270 sec
* **Minimum response time**: 0.218 sec
* **Maximum response time**: 0.317 sec
* **Result**: **PASS**

## 2. Company Profile Performance

Benchmarks measured the data-loading path (database queries, file reads, and in-memory Pandas filtering) for 5 representative tickers.

### Cold Cache (Direct SQL queries per ticker)
| Ticker | Load Time | Target | Result |
|--------|-----------|--------|--------|
| TCS    | 0.0209s   | < 3.0s | PASS   |
| RELIANCE| 0.0187s  | < 3.0s | PASS   |
| INFY   | 0.0255s   | < 3.0s | PASS   |
| HDFCBANK| 0.0172s  | < 3.0s | PASS   |
| ITC    | 0.0154s   | < 3.0s | PASS   |

### Warm Cache (Streamlit `@st.cache_data` in-memory filtering)
| Ticker | Load Time | Target | Result |
|--------|-----------|--------|--------|
| TCS    | 0.0044s   | < 3.0s | PASS   |
| RELIANCE| 0.0037s  | < 3.0s | PASS   |
| INFY   | 0.0030s   | < 3.0s | PASS   |
| HDFCBANK| 0.0042s  | < 3.0s | PASS   |
| ITC    | 0.0033s   | < 3.0s | PASS   |

* **Result**: **PASS**

## 3. FastAPI + Streamlit Integration

* **FastAPI port**: 8000
* **Streamlit port**: 8501
* **Port conflict**: None (both servers executed simultaneously on their respective ports)
* **Dashboard loading**: Verified successfully via browser subagent. Home page, Company Profile page, and sector metrics render without errors.
* **API/Database Data Integration**: Note that the Streamlit dashboard reads financial datasets directly from the SQLite database via cached helper functions (in `src/dashboard/utils/db.py`) and filters them using Pandas, rather than calling the FastAPI endpoints. Both components utilize the same database (`data/nifty100.db`) ensuring data consistency.
* **Result**: **PASS**

## 4. SQLite Optimization

We analyzed the table structures and query plans using `EXPLAIN QUERY PLAN` for the primary data-fetching statements.

### Queries Investigated & Plans:
1. **Fetch Company details**:
   * **SQL**: `SELECT * FROM companies WHERE id = 'TCS'`
   * **Plan**: `SEARCH companies USING INDEX sqlite_autoindex_companies_1 (id=?)` (O(log N) lookup)
2. **Fetch Sector details**:
   * **SQL**: `SELECT * FROM sectors WHERE company_id = 'TCS'`
   * **Plan**: `SEARCH sectors USING INDEX idx_sectors_company_id (company_id=?)` (O(log N) lookup)
3. **Fetch Financial Ratios**:
   * **SQL**: `SELECT * FROM financial_ratios WHERE company_id = 'TCS'`
   * **Plan**: `SEARCH financial_ratios USING INDEX sqlite_autoindex_financial_ratios_1 (company_id=?)` (O(log N) lookup via Unique constraint index)
4. **Fetch Profit & Loss**:
   * **SQL**: `SELECT * FROM profitandloss WHERE company_id = 'TCS'`
   * **Plan**: `SEARCH profitandloss USING INDEX idx_pl_company_year (company_id=?)` (O(log N) lookup via Composite primary key index)
5. **Fetch Stock Prices**:
   * **SQL**: `SELECT * FROM stock_prices WHERE company_id = 'TCS' AND date = '2026-08-14'`
   * **Plan**: `SEARCH stock_prices USING INDEX sqlite_autoindex_stock_prices_1 (company_id=? AND date=?)` (O(log N) lookup)

### Index Assessment:
All primary queries utilize indexed search paths. Because composite primary keys and unique constraints (`UNIQUE (company_id, year)` on `financial_ratios`) automatically create index structures in SQLite, and indexes exist on `sectors(company_id)` and `documents(company_id)`, no full-table scans (`SCAN`) are executed during profile rendering. No additional indexes are required.

## 5. Bottlenecks

1. **Initial Streamlit App Load (Cold Boot)**:
   * **Description**: The very first time the Streamlit dashboard is opened, it loads package dependencies and queries the complete database tables to warm up its in-memory dataframes. This causes a minor cold boot latency (~1 second).
   * **Mitigation**: Streamlit's `@st.cache_data` caching keeps the data pre-loaded for subsequent user requests, reducing ticker search and page change load times to < 5ms.
2. **Synchronous DB Access in API**:
   * **Description**: The FastAPI server accesses SQLite using the synchronous `sqlite3` library. While read queries are extremely fast, concurrent writes would block due to SQLite's database-level lock.
   * **Mitigation**: Since the API screener is primarily a read-only endpoint, read queries are concurrently handled safely and performantly by the operating system's filesystem cache.

## 6. Final Result

**PASS**
