from typing import Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.api.database import get_db_connection, clean_dict_nans, clean_df_nans

router = APIRouter(tags=["Sectors"])


@router.get("/sector")
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
