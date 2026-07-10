-- Schema for Nifty 100 Financial Intelligence Platform

-- Table for Nifty 100 companies metadata
CREATE TABLE IF NOT EXISTS companies (
    symbol TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    sector TEXT NOT NULL,
    industry TEXT,
    isin_code TEXT UNIQUE,
    weightage REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for daily stock price data
CREATE TABLE IF NOT EXISTS daily_prices (
    symbol TEXT,
    date DATE,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    adj_close REAL NOT NULL,
    volume INTEGER NOT NULL,
    PRIMARY KEY (symbol, date),
    FOREIGN KEY (symbol) REFERENCES companies (symbol) ON DELETE CASCADE
);

-- Table for financial metrics
CREATE TABLE IF NOT EXISTS financial_metrics (
    symbol TEXT,
    pe_ratio REAL,
    pb_ratio REAL,
    dividend_yield REAL,
    market_cap REAL,
    eps REAL,
    beta REAL,
    fifty_two_week_high REAL,
    fifty_two_week_low REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol),
    FOREIGN KEY (symbol) REFERENCES companies (symbol) ON DELETE CASCADE
);

-- Table for ETL execution logs
CREATE TABLE IF NOT EXISTS etl_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL, -- 'SUCCESS', 'FAILED'
    records_inserted INTEGER DEFAULT 0,
    error_message TEXT
);
