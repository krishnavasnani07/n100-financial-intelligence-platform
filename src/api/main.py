"""
REST API Engine.
Exposes FastAPI endpoints for company, sector, screener, peer comparison, and valuation data.
Includes automatic Swagger documentation.
Cleans pandas NaN values to None to prevent JSON serialization errors.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import DB_PATH

app = FastAPI(
    title="Nifty 100 Financial Intelligence API",
    description="REST API backend exposing company ratios, sector summaries, screeners, valuations, and peer comparisons.",
    version="1.0.0",
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
        "status": "healthy",
    }


# ==========================================
# Day 39 REST API Endpoints
# ==========================================


@app.get("/companies")
def get_companies():
    """
    Returns a list of all companies with their ID, name, sector, and sub-sector.
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT c.id, c.company_name, s.broad_sector, s.sub_sector
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        ORDER BY c.id ASC
        """
        df = pd.read_sql_query(query, conn)
        return clean_df_nans(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    finally:
        conn.close()


@app.get("/company/{ticker}")
def get_company_details(ticker: str):
    """
    Returns general details and the latest year's financial ratios/KPIs for a specific company ticker.
    """
    conn = get_db_connection()
    try:
        # Load latest ratio record
        query = """
        SELECT * FROM financial_ratios 
        WHERE UPPER(company_id) = UPPER(?) 
        ORDER BY id DESC LIMIT 1
        """
        row = conn.execute(query, [ticker]).fetchone()

        if not row:
            raise HTTPException(
                status_code=404, detail=f"Company with ticker '{ticker}' not found."
            )

        # Get sector info
        sector_row = conn.execute(
            "SELECT broad_sector, sub_sector, market_cap_category FROM sectors WHERE UPPER(company_id) = UPPER(?)",
            [ticker],
        ).fetchone()

        # Get company metadata
        company_row = conn.execute(
            "SELECT company_name, about_company, website, book_value, face_value FROM companies WHERE UPPER(id) = UPPER(?)",
            [ticker],
        ).fetchone()

        data = dict(row)
        if sector_row:
            data.update(dict(sector_row))
        if company_row:
            data.update(dict(company_row))

        return clean_dict_nans(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    finally:
        conn.close()


@app.get("/valuation")
def get_valuation():
    """
    Triggers the valuation engine to compute and return PE, PB, EV/EBITDA, FCF Yield,
    5Y Median PE, and Valuation Flags for all constituents.
    """
    from src.analytics.valuation import run_valuation_pipeline

    try:
        df = run_valuation_pipeline(DB_PATH)
        return clean_df_nans(df)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Valuation pipeline execution error: {e}"
        )


@app.get("/screen")
def screen_companies(
    preset: Optional[str] = Query(
        None, description="Preset strategy name (e.g. 'Value Pick')"
    )
):
    """
    Executes an investment screener preset and returns matching companies.
    If no preset is provided, returns the list of available presets.
    """
    from src.screener.presets import load_screener_master_data, run_preset

    available_presets = [
        "Quality Compounder",
        "Value Pick",
        "Growth Accelerator",
        "Dividend Champion",
        "Debt-Free Blue Chip",
        "Turnaround Watch",
    ]

    if not preset:
        return {
            "available_presets": available_presets,
            "message": "Use ?preset=<name> to screen companies.",
        }

    # Match case-insensitively
    matching_preset = next(
        (p for p in available_presets if p.lower() == preset.lower()), None
    )
    if not matching_preset:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid preset '{preset}'. Available presets: {available_presets}",
        )

    try:
        master_df = load_screener_master_data(DB_PATH)
        matched_df = run_preset(matching_preset, master_df)
        return clean_df_nans(matched_df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screener execution error: {e}")


@app.get("/sector")
def get_sector_info(
    name: Optional[str] = Query(None, description="Sector name (e.g. 'IT')")
):
    """
    Returns statistics and list of companies for a given sector name.
    If no sector name is provided, returns summary stats for all sectors.
    """
    conn = get_db_connection()
    try:
        if name:
            query = """
            SELECT c.id, c.company_name, s.broad_sector, s.sub_sector, s.market_cap_category 
            FROM companies c
            JOIN sectors s ON c.id = s.company_id
            WHERE LOWER(s.broad_sector) = LOWER(?)
            """
            rows = conn.execute(query, [name]).fetchall()

            if not rows:
                raise HTTPException(
                    status_code=404,
                    detail=f"Sector '{name}' has no records or does not exist.",
                )

            companies = [clean_dict_nans(dict(r)) for r in rows]

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
            stats_row = conn.execute(query_stats, [name]).fetchone()

            return {
                "sector": name,
                "companies_count": len(companies),
                "statistics": clean_dict_nans(dict(stats_row)) if stats_row else {},
                "companies": companies,
            }
        else:
            query = """
            SELECT 
                s.broad_sector as sector,
                COUNT(c.id) as companies_count,
                AVG(fr.return_on_equity_pct) as avg_roe,
                AVG(fr.return_on_capital_employed_pct) as avg_roce,
                AVG(fr.debt_to_equity) as avg_debt_to_equity,
                AVG(fr.operating_profit_margin_pct) as avg_margin
            FROM companies c
            JOIN sectors s ON c.id = s.company_id
            LEFT JOIN financial_ratios fr ON c.id = fr.company_id
            GROUP BY s.broad_sector
            ORDER BY companies_count DESC
            """
            df = pd.read_sql_query(query, conn)
            return clean_df_nans(df)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sector query error: {e}")
    finally:
        conn.close()


@app.get("/peer")
def get_peer_comparison(
    sector: Optional[str] = Query(None, description="Sector name to filter peers")
):
    """
    Returns peer comparisons, top performers, and sector statistics.
    If a sector name is provided, filters the results to that specific sector.
    """
    try:
        from src.peer_analysis.comparison import run_peer_analysis

        peer_comp_df, bottom_perf_df, top_perf_df, sector_stats_df = run_peer_analysis(
            DB_PATH
        )

        if sector:
            # Normalize and filter
            peer_comp_df = peer_comp_df[
                peer_comp_df["Sector"].str.lower() == sector.lower()
            ]
            bottom_perf_df = bottom_perf_df[
                bottom_perf_df["Sector"].str.lower() == sector.lower()
            ]
            top_perf_df = top_perf_df[
                top_perf_df["Sector"].str.lower() == sector.lower()
            ]
            sector_stats_df = sector_stats_df[
                sector_stats_df["Sector"].str.lower() == sector.lower()
            ]

        return {
            "peer_comparison": clean_df_nans(peer_comp_df),
            "top_performers": clean_df_nans(top_perf_df),
            "bottom_performers": clean_df_nans(bottom_perf_df),
            "sector_statistics": clean_df_nans(sector_stats_df),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Peer analysis execution error: {e}"
        )


# ==========================================
# Legacy/Compatibility Routes
# ==========================================


@app.get("/api/company/{company_id}")
def get_company_ratios(company_id: str):
    """Legacy route to fetch company details."""
    return get_company_details(company_id)


@app.get("/api/sector/{sector_name}")
def get_sector_data(sector_name: str):
    """Legacy route to fetch sector details."""
    return get_sector_info(sector_name)


@app.get("/api/screener/{preset_name}")
def run_screener_preset(preset_name: str):
    """Legacy route to run screener presets."""
    return screen_companies(preset_name)


@app.get("/api/topperformers")
def get_top_performers():
    """Legacy route to fetch top performers."""
    conn = get_db_connection()
    try:
        from src.peer_analysis.comparison import run_peer_analysis

        _, _, top_perf_df, _ = run_peer_analysis(DB_PATH)
        return clean_df_nans(top_perf_df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/api/peercomparison")
def get_peer_comparison_legacy():
    """Legacy route to fetch peer comparison."""
    conn = get_db_connection()
    try:
        from src.peer_analysis.comparison import run_peer_analysis

        peer_comp_df, _, _, _ = run_peer_analysis(DB_PATH)
        return clean_df_nans(peer_comp_df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
