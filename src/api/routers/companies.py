import pandas as pd
from fastapi import APIRouter, HTTPException

from src.api.database import get_db_connection, clean_dict_nans, clean_df_nans

router = APIRouter(tags=["Companies"])


@router.get("/companies")
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


@router.get("/company/{ticker}")
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
