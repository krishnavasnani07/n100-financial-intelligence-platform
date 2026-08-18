import time
import sqlite3
import pandas as pd
from pathlib import Path
from src.config import settings

TICKERS = ["TCS", "RELIANCE", "INFY", "HDFCBANK", "ITC"]

def benchmark_ticker_cold(ticker, db_path):
    """Simulates loading data directly from SQLite for a single ticker (Cold Cache scenario)."""
    start = time.perf_counter()
    conn = sqlite3.connect(db_path)
    try:
        # Replicate SQL queries
        company_df = pd.read_sql_query("SELECT * FROM companies WHERE id = ?", conn, params=[ticker])
        sector_df = pd.read_sql_query("SELECT * FROM sectors WHERE company_id = ?", conn, params=[ticker])
        ratios_df = pd.read_sql_query("SELECT * FROM financial_ratios WHERE company_id = ?", conn, params=[ticker])
        pl_df = pd.read_sql_query("SELECT * FROM profitandloss WHERE company_id = ?", conn, params=[ticker])
        
        # Replicate CSV loads
        alloc_path = Path("output/capital_allocation.csv")
        if alloc_path.exists():
            df_alloc = pd.read_csv(alloc_path)
            df_comp_alloc = df_alloc[df_alloc["company_id"] == ticker]
            
        changes_path = Path("output/pattern_changes.csv")
        if changes_path.exists():
            df_changes = pd.read_csv(changes_path)
            df_comp_changes = df_changes[df_changes["company_id"] == ticker]
            
    finally:
        conn.close()
        
    duration = time.perf_counter() - start
    return duration

def benchmark_ticker_warm(ticker, df_companies, df_sectors, df_ratios, df_pl, df_alloc, df_changes):
    """Simulates filtering already loaded/cached tables in memory (Warm Cache scenario)."""
    start = time.perf_counter()
    
    # Filter in memory
    company_info = df_companies[df_companies["id"] == ticker]
    sector_info = df_sectors[df_sectors["company_id"] == ticker]
    df_company_ratios = df_ratios[df_ratios["company_id"] == ticker]
    df_company_pl = df_pl[df_pl["company_id"] == ticker]
    
    if df_alloc is not None:
        df_comp_alloc = df_alloc[df_alloc["company_id"] == ticker]
    if df_changes is not None:
        df_comp_changes = df_changes[df_changes["company_id"] == ticker]
        
    duration = time.perf_counter() - start
    return duration

def run_benchmarks():
    db_path = settings.DB_PATH
    if not Path(db_path).exists():
        print(f"ERROR: Database not found at {db_path}.")
        return False
        
    print("Pre-loading entire dataset in memory (simulating Streamlit Cache warm-up)...")
    conn = sqlite3.connect(db_path)
    df_companies = pd.read_sql_query("SELECT * FROM companies", conn)
    df_sectors = pd.read_sql_query("SELECT * FROM sectors", conn)
    df_ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    df_pl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    conn.close()
    
    df_alloc = pd.read_csv("output/capital_allocation.csv") if Path("output/capital_allocation.csv").exists() else None
    df_changes = pd.read_csv("output/pattern_changes.csv") if Path("output/pattern_changes.csv").exists() else None

    print("\n--- Cold Cache Latency (Direct SQL queries) ---")
    cold_results = {}
    for ticker in TICKERS:
        dur = benchmark_ticker_cold(ticker, db_path)
        cold_results[ticker] = dur
        print(f"Ticker: {ticker:8} | Load Time: {dur:.4f}s | Result: {'PASS' if dur < 3.0 else 'FAIL'}")
        assert dur < 3.0, f"Cold cache load for {ticker} took {dur:.2f}s (target < 3s)"
        
    print("\n--- Warm Cache Latency (In-memory Filtering) ---")
    warm_results = {}
    for ticker in TICKERS:
        dur = benchmark_ticker_warm(ticker, df_companies, df_sectors, df_ratios, df_pl, df_alloc, df_changes)
        warm_results[ticker] = dur
        print(f"Ticker: {ticker:8} | Load Time: {dur:.4f}s | Result: {'PASS' if dur < 3.0 else 'FAIL'}")
        assert dur < 3.0, f"Warm cache load for {ticker} took {dur:.2f}s (target < 3s)"

    print("\nAll company profile benchmarks successfully completed!")
    return True

if __name__ == "__main__":
    run_benchmarks()
