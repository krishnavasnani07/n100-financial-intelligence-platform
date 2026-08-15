from typing import Optional, Dict, Any, List
import sqlite3
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.api.database import get_db_connection, clean_dict_nans, clean_df_nans
from src.config.settings import DB_PATH, OUTPUT_DIR
from src.reports.report_utils import map_sector
from src.screener.ranking import calculate_rankings

router = APIRouter(tags=["Sectors"])

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


@router.get("/sector")
def get_sector_info(
    name: Optional[str] = Query(None, description="Sector name (e.g. 'IT')")
):
    """
    Legacy route to return statistics and list of companies for a given sector name.
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


@router.get("/sectors")
def get_sectors():
    """
    Returns statistics (median ROE, PE, DE, and company counts) for all 11 standardized sectors.
    """
    try:
        csv_path = OUTPUT_DIR / "csv" / "rankings.csv"
        if not csv_path.exists():
            df = calculate_rankings(DB_PATH)
        else:
            df = pd.read_csv(csv_path)

        df["sector_standardized"] = df.apply(
            lambda r: map_sector(r.get("sector"), r.get("sub_sector")), axis=1
        )

        results = []
        for sector in VALID_SECTORS:
            sec_df = df[df["sector_standardized"] == sector]
            count = len(sec_df)
            if count > 0:
                median_roe = sec_df["return_on_equity_pct"].median()
                median_pe = sec_df["pe"].median()
                median_de = sec_df["debt_to_equity"].median()
            else:
                median_roe = 0.0
                median_pe = 0.0
                median_de = 0.0

            results.append(clean_dict_nans({
                "sector": sector,
                "company_count": count,
                "median_roe": None if pd.isna(median_roe) else round(float(median_roe), 2),
                "median_pe": None if pd.isna(median_pe) else round(float(median_pe), 2),
                "median_de": None if pd.isna(median_de) else round(float(median_de), 2),
            }))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sectors query error: {e}")


@router.get("/sectors/{sector}/companies")
def get_sector_companies(sector: str):
    """
    Returns companies belonging to the requested standardized sector.
    """
    normalized = normalize_sector_name(sector)
    if not normalized:
        raise HTTPException(
            status_code=404,
            detail=f"Sector '{sector}' does not exist.",
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

        sec_df = df[df["sector_standardized"] == normalized]

        companies_map = get_companies_map()
        results = []
        for _, row in sec_df.iterrows():
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
        raise HTTPException(status_code=500, detail=f"Sectors query error: {e}")

