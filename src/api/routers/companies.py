import csv
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.api.database import get_db_connection, clean_dict_nans, clean_df_nans

router = APIRouter(tags=["Companies"])


# ==========================================
# Pydantic Response Models
# ==========================================


class CompanySummary(BaseModel):
    id: str
    ticker: str
    company_name: str
    sector: Optional[str] = None
    broad_sector: Optional[str] = None
    sub_sector: Optional[str] = None
    market_cap_category: Optional[str] = None
    roe: Optional[float] = None
    roce: Optional[float] = None


class CompaniesResponse(BaseModel):
    count: int
    companies: List[CompanySummary]


class CompanyProfile(BaseModel):
    id: str
    company_id: str
    ticker: str
    company_name: str
    about_company: Optional[str] = None
    website: Optional[str] = None
    book_value: Optional[float] = None
    face_value: Optional[float] = None
    broad_sector: Optional[str] = None
    sector: Optional[str] = None
    sub_sector: Optional[str] = None
    market_cap_category: Optional[str] = None
    latest_year: Optional[int] = None
    kpis: Dict[str, Any] = {}
    pros: List[str] = []
    cons: List[str] = []


# ==========================================
# API Endpoints
# ==========================================


@router.get("/companies", response_model=CompaniesResponse)
def get_companies(
    sector: Optional[str] = Query(None, description="Broad sector to filter by"),
    market_cap_category: Optional[str] = Query(
        None, description="Market cap category to filter by"
    ),
    search: Optional[str] = Query(
        None, description="Partial search on ticker or company name"
    ),
):
    """
    Returns a list of all companies with their ID, name, sector, sub-sector, market cap category, ROE, and ROCE.
    Supports query parameters for filtering and searching.
    """
    conn = get_db_connection()
    try:
        query = """
        SELECT c.id as id, c.id as ticker, c.company_name, 
               s.broad_sector, s.broad_sector as sector, s.sub_sector, s.market_cap_category,
               c.roe_percentage as roe, c.roce_percentage as roce
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        """
        where_clauses = []
        params = []

        if sector:
            where_clauses.append("LOWER(s.broad_sector) = LOWER(?)")
            params.append(sector.strip())

        if market_cap_category:
            where_clauses.append("LOWER(s.market_cap_category) = LOWER(?)")
            params.append(market_cap_category.strip())

        if search:
            where_clauses.append("(LOWER(c.id) LIKE ? OR LOWER(c.company_name) LIKE ?)")
            search_pattern = f"%{search.strip().lower()}%"
            params.extend([search_pattern, search_pattern])

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY c.id ASC"
        df = pd.read_sql_query(query, conn, params=params)
        companies_list = clean_df_nans(df)
        return {"count": len(companies_list), "companies": companies_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    finally:
        conn.close()


@router.get("/companies/{ticker}", response_model=CompanyProfile)
def get_company_details(ticker: str):
    """
    Returns general details and the latest year's financial ratios/KPIs, sector details,
    as well as pros and cons from pre-analyzed outputs for a specific company ticker.
    """
    ticker = ticker.upper().strip()
    conn = get_db_connection()
    try:
        company_row = conn.execute(
            "SELECT * FROM companies WHERE UPPER(id) = UPPER(?)", [ticker]
        ).fetchone()
        if not company_row:
            raise HTTPException(
                status_code=404,
                detail=f"Company ticker '{ticker}' not found",
            )

        # Get sector info
        sector_row = conn.execute(
            "SELECT broad_sector, sub_sector, market_cap_category FROM sectors WHERE UPPER(company_id) = UPPER(?)",
            [ticker],
        ).fetchone()

        # Get all financial ratio rows for the company
        ratio_rows = conn.execute(
            "SELECT * FROM financial_ratios WHERE UPPER(company_id) = UPPER(?)",
            [ticker],
        ).fetchall()

        # Helper to parse year string to integer
        def parse_year_to_int(year_str):
            if str(year_str).upper().strip() == "TTM":
                return 0  # ignore TTM for profile default latest year
            try:
                digits = "".join(c for c in str(year_str) if c.isdigit())
                if len(digits) >= 4:
                    return int(digits[-4:])
                return int(digits) if digits else 0
            except ValueError:
                return 0

        latest_row = None
        latest_year = None
        max_parsed_year = -1

        for r in ratio_rows:
            parsed_yr = parse_year_to_int(r["year"])
            if parsed_yr > max_parsed_year:
                max_parsed_year = parsed_yr
                latest_row = r
                # We can save latest_year as the original year string or parsed_yr.
                # Let's save it as the integer parsed_yr.
                latest_year = parsed_yr

        kpis = {}
        if latest_row:
            kpis = clean_dict_nans(dict(latest_row))

        # Read pros and cons
        pros = []
        cons = []
        csv_path = Path("output/pros_cons_generated.csv")
        if csv_path.exists():
            with open(csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["company_id"].upper().strip() == ticker:
                        text = row["text"].strip()
                        if row["type"].upper().strip() == "PRO":
                            pros.append(text)
                        elif row["type"].upper().strip() == "CON":
                            cons.append(text)

        comp_dict = dict(company_row)
        sec_dict = dict(sector_row) if sector_row else {}

        response_data = {
            "id": comp_dict.get("id"),
            "company_id": comp_dict.get("id"),
            "ticker": comp_dict.get("id"),
            "company_name": comp_dict.get("company_name"),
            "about_company": comp_dict.get("about_company"),
            "website": comp_dict.get("website"),
            "book_value": comp_dict.get("book_value"),
            "face_value": comp_dict.get("face_value"),
            "broad_sector": sec_dict.get("broad_sector"),
            "sector": sec_dict.get("broad_sector"),
            "sub_sector": sec_dict.get("sub_sector"),
            "market_cap_category": sec_dict.get("market_cap_category"),
            "latest_year": latest_year,
            "kpis": kpis,
            "pros": pros,
            "cons": cons,
        }
        return clean_dict_nans(response_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    finally:
        conn.close()


@router.get("/companies/{ticker}/pl")
def get_company_pl(
    ticker: str,
    from_year: Optional[int] = Query(None, description="Filter from year (inclusive)"),
    to_year: Optional[int] = Query(None, description="Filter to year (inclusive)"),
):
    """
    Returns the company's historical P&L records, with optional from_year and to_year filters.
    """
    ticker = ticker.upper().strip()
    if from_year is not None and to_year is not None and from_year > to_year:
        raise HTTPException(
            status_code=400, detail="from_year cannot be greater than to_year"
        )

    conn = get_db_connection()
    try:
        # Check company existence
        company_exists = conn.execute(
            "SELECT 1 FROM companies WHERE UPPER(id) = UPPER(?)", [ticker]
        ).fetchone()
        if not company_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Company ticker '{ticker}' not found",
            )

        query = "SELECT * FROM profitandloss WHERE UPPER(company_id) = UPPER(?)"
        params = [ticker]
        df = pd.read_sql_query(query, conn, params=params)

        def parse_year_to_int(year_str):
            if str(year_str).upper().strip() == "TTM":
                return 9999
            try:
                digits = "".join(c for c in str(year_str) if c.isdigit())
                if len(digits) >= 4:
                    return int(digits[-4:])
                return int(digits) if digits else 0
            except ValueError:
                return 0

        if not df.empty:
            df["parsed_year"] = df["year"].apply(parse_year_to_int)
            if from_year is not None:
                df = df[df["parsed_year"] >= from_year]
            if to_year is not None:
                df = df[df["parsed_year"] <= to_year]

            df = df.sort_values(by="parsed_year", ascending=True)
            df = df.drop(columns=["parsed_year"])

        return clean_df_nans(df)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    finally:
        conn.close()


@router.get("/companies/{ticker}/bs")
def get_company_bs(
    ticker: str,
    from_year: Optional[int] = Query(None, description="Filter from year (inclusive)"),
    to_year: Optional[int] = Query(None, description="Filter to year (inclusive)"),
):
    """
    Returns the company's historical Balance Sheet records, with optional from_year and to_year filters.
    """
    ticker = ticker.upper().strip()
    if from_year is not None and to_year is not None and from_year > to_year:
        raise HTTPException(
            status_code=400, detail="from_year cannot be greater than to_year"
        )

    conn = get_db_connection()
    try:
        # Check company existence
        company_exists = conn.execute(
            "SELECT 1 FROM companies WHERE UPPER(id) = UPPER(?)", [ticker]
        ).fetchone()
        if not company_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Company ticker '{ticker}' not found",
            )

        query = "SELECT * FROM balancesheet WHERE UPPER(company_id) = UPPER(?)"
        params = [ticker]
        df = pd.read_sql_query(query, conn, params=params)

        def parse_year_to_int(year_str):
            if str(year_str).upper().strip() == "TTM":
                return 9999
            try:
                digits = "".join(c for c in str(year_str) if c.isdigit())
                if len(digits) >= 4:
                    return int(digits[-4:])
                return int(digits) if digits else 0
            except ValueError:
                return 0

        if not df.empty:
            df["parsed_year"] = df["year"].apply(parse_year_to_int)
            if from_year is not None:
                df = df[df["parsed_year"] >= from_year]
            if to_year is not None:
                df = df[df["parsed_year"] <= to_year]

            df = df.sort_values(by="parsed_year", ascending=True)
            df = df.drop(columns=["parsed_year"])

        return clean_df_nans(df)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    finally:
        conn.close()


@router.get("/companies/{ticker}/cashflow")
def get_company_cashflow(
    ticker: str,
    from_year: Optional[int] = Query(None, description="Filter from year (inclusive)"),
    to_year: Optional[int] = Query(None, description="Filter to year (inclusive)"),
):
    """
    Returns the company's historical Cash Flow records, with optional from_year and to_year filters.
    """
    ticker = ticker.upper().strip()
    if from_year is not None and to_year is not None and from_year > to_year:
        raise HTTPException(
            status_code=400, detail="from_year cannot be greater than to_year"
        )

    conn = get_db_connection()
    try:
        # Check company existence
        company_exists = conn.execute(
            "SELECT 1 FROM companies WHERE UPPER(id) = UPPER(?)", [ticker]
        ).fetchone()
        if not company_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Company ticker '{ticker}' not found",
            )

        query = "SELECT * FROM cashflow WHERE UPPER(company_id) = UPPER(?)"
        params = [ticker]
        df = pd.read_sql_query(query, conn, params=params)

        def parse_year_to_int(year_str):
            if str(year_str).upper().strip() == "TTM":
                return 9999
            try:
                digits = "".join(c for c in str(year_str) if c.isdigit())
                if len(digits) >= 4:
                    return int(digits[-4:])
                return int(digits) if digits else 0
            except ValueError:
                return 0

        if not df.empty:
            df["parsed_year"] = df["year"].apply(parse_year_to_int)
            if from_year is not None:
                df = df[df["parsed_year"] >= from_year]
            if to_year is not None:
                df = df[df["parsed_year"] <= to_year]

            df = df.sort_values(by="parsed_year", ascending=True)
            df = df.drop(columns=["parsed_year"])

        return clean_df_nans(df)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    finally:
        conn.close()


@router.get("/companies/{ticker}/ratios")
def get_company_ratios(
    ticker: str,
    year: Optional[int] = Query(None, description="Filter by specific year"),
):
    """
    Returns the company's historical financial ratios, with optional year filter.
    Includes custom interest coverage ratio labelling.
    """
    ticker = ticker.upper().strip()
    conn = get_db_connection()
    try:
        # Check company existence
        company_exists = conn.execute(
            "SELECT 1 FROM companies WHERE UPPER(id) = UPPER(?)", [ticker]
        ).fetchone()
        if not company_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Company ticker '{ticker}' not found",
            )

        query = "SELECT * FROM financial_ratios WHERE UPPER(company_id) = UPPER(?)"
        params = [ticker]
        df = pd.read_sql_query(query, conn, params=params)

        def parse_year_to_int(year_str):
            if str(year_str).upper().strip() == "TTM":
                return 9999
            try:
                digits = "".join(c for c in str(year_str) if c.isdigit())
                if len(digits) >= 4:
                    return int(digits[-4:])
                return int(digits) if digits else 0
            except ValueError:
                return 0

        if not df.empty:
            df["parsed_year"] = df["year"].apply(parse_year_to_int)
            if year is not None:
                df = df[df["parsed_year"] == year]
            df = df.sort_values(by="parsed_year", ascending=True)
            df = df.drop(columns=["parsed_year"])

        ratios_list = clean_df_nans(df)

        # Add dynamic icr_label to each ratio dictionary
        for r in ratios_list:
            icr = r.get("interest_coverage")
            # If interest_coverage is None or NaN, icr_label is "Debt Free"
            if icr is None or pd.isna(icr):
                r["interest_coverage"] = None
                r["icr_label"] = "Debt Free"
            else:
                try:
                    icr_val = float(icr)
                    if icr_val >= 5.0:
                        r["icr_label"] = "Excellent"
                    elif icr_val >= 2.0:
                        r["icr_label"] = "Good"
                    elif icr_val >= 1.5:
                        r["icr_label"] = "Average"
                    else:
                        r["icr_label"] = "Critical"
                except (ValueError, TypeError):
                    r["icr_label"] = "Debt Free"

        return ratios_list
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    finally:
        conn.close()


@router.get("/companies/{ticker}/tearsheet")
def get_company_tearsheet(ticker: str):
    """
    Returns the pre-generated company tearsheet PDF as a binary download file response.
    Returns a 404 if the company ticker is invalid or the tearsheet PDF is missing.
    """
    ticker = ticker.upper().strip()
    conn = get_db_connection()
    try:
        # Check company existence
        company_exists = conn.execute(
            "SELECT 1 FROM companies WHERE UPPER(id) = UPPER(?)", [ticker]
        ).fetchone()
        if not company_exists:
            raise HTTPException(
                status_code=404,
                detail=f"Company ticker '{ticker}' not found",
            )
    finally:
        conn.close()

    # Form path
    pdf_path = Path("reports/tearsheets") / f"{ticker}_tearsheet.pdf"
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Tearsheet PDF for company '{ticker}' not found",
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{ticker}_tearsheet.pdf",
    )
