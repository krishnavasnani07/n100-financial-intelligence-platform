"""
REST API Engine.
Exposes FastAPI endpoints for company, sector, screener, and peer comparison data.
Includes automatic Swagger documentation.
Cleans pandas NaN values to None to prevent JSON serialization errors.
"""

from __future__ import annotations
import sqlite3
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import DB_PATH

app = FastAPI(
    title="Nifty 100 Financial Intelligence API",
    description="REST API backend exposing company ratios, sector summaries, screeners, and peer comparisons.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def clean_dict_nans(d: Dict[str, Any]) -> Dict[str, Any]:
    """Replaces any NaN values in a dictionary with None (JSON null)."""
    return {k: (None if pd.isna(v) else v) for k, v in d.items()}


def clean_df_nans(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Replaces any NaN values in a DataFrame with None and returns record dictionaries."""
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    return [clean_dict_nans(r) for r in records]


@app.get("/")
def read_root():
    return {
        "app": "Nifty 100 Financial Intelligence API",
        "docs": "/docs",
        "status": "healthy"
    }


@app.get("/api/company/{company_id}")
def get_company_ratios(company_id: str):
    """
    Returns the latest year financial ratios for a given company.
    """
    conn = get_db_connection()
    try:
        # Load latest ratio record
        query = """
        SELECT * FROM financial_ratios 
        WHERE company_id = ? 
        ORDER BY id DESC LIMIT 1
        """
        row = conn.execute(query, [company_id.upper()]).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Company '{company_id}' not found.")
            
        # Get sector info
        sector_row = conn.execute("SELECT broad_sector, sub_sector, market_cap_category FROM sectors WHERE company_id = ?", [company_id.upper()]).fetchone()
        
        data = dict(row)
        if sector_row:
            data.update(dict(sector_row))
            
        return clean_dict_nans(data)
    finally:
        conn.close()


@app.get("/api/sector/{sector_name}")
def get_sector_data(sector_name: str):
    """
    Returns companies and statistics for a given sector.
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT c.id, c.company_name, s.broad_sector, s.sub_sector, s.market_cap_category 
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        WHERE LOWER(s.broad_sector) = LOWER(?)
        """
        rows = conn.execute(query, [sector_name]).fetchall()
        
        if not rows:
            raise HTTPException(status_code=404, detail=f"Sector '{sector_name}' has no records or does not exist.")
            
        companies = [clean_dict_nans(dict(r)) for r in rows]
        
        # Calculate some summary statistics for the sector
        query_stats = """
        SELECT 
            AVG(fr.return_on_equity_pct) as avg_roe,
            AVG(fr.return_on_capital_employed_pct) as avg_roce,
            AVG(fr.debt_to_equity) as avg_debt_to_equity,
            AVG(fr.operating_profit_margin_pct) as avg_margin
        FROM financial_ratios fr
        JOIN sectors s ON fr.company_id = s.company_id
        WHERE LOWER(s.broad_sector) = LOWER(?)
        """
        stats_row = conn.execute(query_stats, [sector_name]).fetchone()
        
        return {
            "sector": sector_name,
            "companies_count": len(companies),
            "statistics": clean_dict_nans(dict(stats_row)) if stats_row else {},
            "companies": companies
        }
    finally:
        conn.close()


@app.get("/api/screener/{preset_name}")
def run_screener_preset(preset_name: str):
    """
    Executes an investment screener preset and returns matching companies.
    
    Available presets:
    - Quality Compounder
    - Value Pick
    - Growth Accelerator
    - Dividend Champion
    - Debt-Free Blue Chip
    - Turnaround Watch
    """
    from src.screener.presets import run_preset, load_screener_master_data
    try:
        master_df = load_screener_master_data(DB_PATH)
        matched_df = run_preset(preset_name, master_df)
        return clean_df_nans(matched_df)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screener execution error: {e}")


@app.get("/api/topperformers")
def get_top_performers():
    """
    Returns the top 3 performing companies per sector.
    """
    try:
        from src.peer_analysis.comparison import run_peer_analysis
        _, _, top_perf_df, _ = run_peer_analysis(DB_PATH)
        return clean_df_nans(top_perf_df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving top performers: {e}")


@app.get("/api/peercomparison")
def get_peer_comparison():
    """
    Returns the complete sector peer comparison and percentile ranking dataset.
    """
    try:
        from src.peer_analysis.comparison import run_peer_analysis
        peer_comp_df, _, _, _ = run_peer_analysis(DB_PATH)
        return clean_df_nans(peer_comp_df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing peer comparison: {e}")
