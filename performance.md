# Performance & Deployment Benchmarks

This report documents the performance metrics, response latencies, and scalability recommendations for the Nifty 100 Financial Intelligence REST API and Dashboard.

## 1. Executive Summary

- **Fastest Endpoint**: `GET /` (Health check) resolves in **2.56ms**.
- **Average API Read Latency**: **11.2ms** (excluding heavy analytics computation).
- **Heaviest Endpoints**:
  - `GET /screen` (Screener Strategy Evaluation): **2.25s** (P95: 3.61s).
  - `GET /peer` (Universal Peer Ranking): **615ms**.
  - `GET /valuation` (Dynamic Excel Generator): **403ms**.
- **Critical Latency Warning**: Using `localhost` as the hostname on Windows systems introduces a **~2.0-second delay** due to IPv6-to-IPv4 DNS resolution timeouts. Querying `127.0.0.1` directly resolves this, improving latencies by over **560x**.

---

## 2. API Response Latency Metrics

*Benchmarks collected over 20 iterations using Python time resolution against host environment (`127.0.0.1:8000`).*

| Endpoint | Min Latency | Average Latency | Max Latency | P95 Latency | Complexity Class |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GET /** (Health Check) | 1.8ms | **2.56ms** | 3.36ms | 3.22ms | O(1) |
| **GET /companies** | 9.2ms | **13.42ms** | 18.28ms | 18.20ms | O(N) |
| **GET /company/TCS** | 6.8ms | **8.15ms** | 9.59ms | 9.48ms | O(1) [Indexed] |
| **GET /sector** | 16.7ms | **24.91ms** | 45.75ms | 36.06ms | O(N) |
| **GET /sector?name=Information+Technology** | 11.9ms | **13.91ms** | 17.53ms | 16.63ms | O(N) |
| **GET /valuation** | 321.8ms | **403.39ms** | 501.56ms | 493.29ms | O(N) + Excel Write |
| **GET /peer** | 554.3ms | **615.02ms** | 671.45ms | 657.56ms | O(N log N) [Math] |
| **GET /peer?sector=Information+Technology** | 176.1ms | **353.48ms** | 607.93ms | 606.16ms | O(N log N) |
| **GET /screen?preset=Value+Pick** | 974.5ms | **2249.51ms** | 3678.69ms | 3608.72ms | O(N²) [Complex Joins] |

---

## 3. Bottleneck Analysis & Observations

1. **Excel Generation Over HTTP (GET /valuation)**:
   - *Observation*: The valuation pipeline generates and writes a styled Excel sheet (`valuation_summary.xlsx`) using `openpyxl` on *every single request*. This accounts for ~90% of the latency (350ms+).
   - *Fix*: Cache the spreadsheet generation. Trigger excel output only when the database is modified or expose a separate async `/export` endpoint.
2. **Screener & Peer Calculations (GET /screen and GET /peer)**:
   - *Observation*: Executing screeners requires joining daily stock price histories (over 300,000 records) to compute CAGR and percentiles dynamically on request.
   - *Fix*: Pre-compute CAGR values in the background scheduler and write them to a dedicated analytics cache table.

---

## 4. Production Deployment & Scaling Guidelines

To prepare the platform for staging and high-concurrency production usage, implement the following configurations:

### 1. ASGI Web Server Tuning (FastAPI)
Deploy FastAPI behind **Gunicorn** using **Uvicorn workers** to utilize multiple CPU cores:
```bash
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
- Rule of thumb for workers: `(2 * CPU Cores) + 1`.

### 2. SQLite Database Optimization
SQLite is extremely fast for reads, but can bottleneck on concurrent writes. Enable **Write-Ahead Logging (WAL) Mode** to allow simultaneous read/write connections:
```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=-64000; -- Cache up to 64MB of pages in memory
```

### 3. Streamlit Frontend Performance (Dashboard)
- Streamlit's default load time is **~120ms** for initial rendering.
- Implement `@st.cache_data` and `@st.cache_resource` for all database calls to ensure page navigations render in `<15ms`.
