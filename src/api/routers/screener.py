from typing import Optional, List, Dict, Any
import sqlite3
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.api.database import clean_df_nans, clean_dict_nans
from src.config.settings import DB_PATH, OUTPUT_DIR
from src.reports.report_utils import map_sector
from src.screener.ranking import calculate_rankings

router = APIRouter(tags=["Screener"])

VALID_SECTORS = [
    "Communication Services",
    "Consumer Discretionary",
    "Consumer Staples",
    "Energy",
    "Banking",
    "Healthcare",
    "Industrials",
    "IT Services",
    "Materials",
    "Real Estate",
    "Utilities"
]


def normalize_sector_name(sector_name: str) -> Optional[str]:
    s = sector_name.strip().upper()
    if s in ["IT", "IT SERVICES", "INFORMATION TECHNOLOGY"]:
        return "IT Services"
    if s in ["FINANCIALS", "BANKING"]:
        return "Banking"
    for val in VALID_SECTORS:
        if val.upper() == s:
            return val
    return None


def get_companies_map() -> Dict[str, str]:
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute("SELECT id, company_name FROM companies").fetchall()
        return {r[0]: r[1] for r in rows}
    except Exception:
        return {}
    finally:
        conn.close()


def safe_float(val: Optional[str], name: str) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        f_val = float(val)
        return f_val
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid value '{val}' for parameter '{name}'. Must be a number.",
        )


@router.get("/screen")
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


@router.get("/screener")
def get_screener(
    min_roe: Optional[str] = Query(None, description="Minimum ROE %"),
    max_de: Optional[str] = Query(None, description="Maximum Debt to Equity ratio"),
    min_fcf: Optional[str] = Query(None, description="Minimum Free Cash Flow (Cr)"),
    sector: Optional[str] = Query(None, description="Standardized sector name"),
    min_rev_cagr_5yr: Optional[str] = Query(None, description="Minimum 5Y Revenue CAGR %"),
    min_pat_cagr_5yr: Optional[str] = Query(None, description="Minimum 5Y PAT CAGR %"),
    max_pe: Optional[str] = Query(None, description="Maximum PE ratio"),
):
    """
    Filters and screens companies based on latest-year KPI metrics.
    """
    # 1. Validate inputs to raise 400 on error
    roe = safe_float(min_roe, "min_roe")
    de = safe_float(max_de, "max_de")
    if de is not None and de < 0:
        raise HTTPException(
            status_code=400,
            detail="Parameter 'max_de' cannot be negative.",
        )
    fcf = safe_float(min_fcf, "min_fcf")
    rev_cagr = safe_float(min_rev_cagr_5yr, "min_rev_cagr_5yr")
    pat_cagr = safe_float(min_pat_cagr_5yr, "min_pat_cagr_5yr")
    pe = safe_float(max_pe, "max_pe")

    normalized_sector = None
    if sector:
        normalized_sector = normalize_sector_name(sector)
        if not normalized_sector:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sector '{sector}'.",
            )

    try:
        csv_path = OUTPUT_DIR / "csv" / "rankings.csv"
        if not csv_path.exists():
            df = calculate_rankings(DB_PATH)
        else:
            df = pd.read_csv(csv_path)

        df["sector_standardized"] = df.apply(
            lambda r: map_sector(r.get("sector"), r.get("sub_sector")), axis=1
        )

        # Apply filtering
        if roe is not None:
            df = df[df["return_on_equity_pct"] >= roe]
        if de is not None:
            df = df[(df["debt_to_equity"] <= de) | (df["sector"].astype(str).str.lower() == "financials")]
        if fcf is not None:
            df = df[df["free_cash_flow_cr"] >= fcf]
        if rev_cagr is not None:
            df = df[df["revenue_cagr_5yr"] >= rev_cagr]
        if pat_cagr is not None:
            df = df[df["pat_cagr_5yr"] >= pat_cagr]
        if pe is not None:
            df = df[df["pe"] <= pe]
        if normalized_sector is not None:
            df = df[df["sector_standardized"] == normalized_sector]

        companies_map = get_companies_map()
        results = []
        for _, row in df.iterrows():
            results.append(clean_dict_nans({
                "company_id": str(row["company_id"]),
                "company_name": companies_map.get(str(row["company_id"]), ""),
                "ticker": str(row["company_id"]),
                "sector": row["sector_standardized"],
                "roe_pct": row["return_on_equity_pct"],
                "debt_to_equity": row["debt_to_equity"],
                "fcf": row["free_cash_flow_cr"],
                "revenue_cagr_5yr": row["revenue_cagr_5yr"],
                "pat_cagr_5yr": row["pat_cagr_5yr"],
                "pe": row.get("pe"),
            }))

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screener query error: {e}")

