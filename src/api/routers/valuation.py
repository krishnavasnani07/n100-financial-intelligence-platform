import sqlite3

import pandas as pd
from fastapi import APIRouter, HTTPException

from src.api.database import clean_df_nans, clean_dict_nans
from src.config.settings import DB_PATH

router = APIRouter(tags=["Valuation"])


@router.get("/valuation")
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


@router.get("/market-cap/{ticker}")
def get_market_cap_history(ticker: str):
    """
    Returns historical valuation multiples (P/E, P/B, EV/EBITDA, Dividend yield) for 2019-2024.
    """
    ticker = ticker.strip().upper()

    # Verify company exists
    conn = sqlite3.connect(DB_PATH)
    try:
        exists = conn.execute(
            "SELECT id FROM companies WHERE UPPER(id) = ?", [ticker]
        ).fetchone()
        if not exists:
            raise HTTPException(
                status_code=404, detail=f"Company '{ticker}' does not exist."
            )
    finally:
        conn.close()

    try:
        from src.config.settings import RAW_DATA_DIR
        from src.utils.helpers import extract_year_int

        path = RAW_DATA_DIR / "market_cap.xlsx"
        if not path.exists():
            raise HTTPException(
                status_code=500, detail="market_cap.xlsx raw data file not found."
            )

        df = pd.read_excel(path)
        df["company_id_clean"] = df["company_id"].astype(str).str.strip().str.upper()
        df_company = df[df["company_id_clean"] == ticker].copy()

        if df_company.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No valuation history found for company '{ticker}'.",
            )

        df_company["year_int"] = df_company["year"].apply(extract_year_int)
        df_company = df_company.dropna(subset=["year_int"])
        df_company["year_int"] = df_company["year_int"].astype(int)

        # Filter for years 2019 to 2024
        df_company = df_company[
            (df_company["year_int"] >= 2019) & (df_company["year_int"] <= 2024)
        ]

        # Sort chronologically by year_int
        df_company = df_company.sort_values(by="year_int")

        history = []
        for _, row in df_company.iterrows():
            history.append(
                clean_dict_nans(
                    {
                        "year": str(int(row["year_int"])),
                        "pe": row.get("pe_ratio"),
                        "pb": row.get("pb_ratio"),
                        "ev_ebitda": row.get("ev_ebitda"),
                        "dividend_yield": row.get("dividend_yield_pct"),
                    }
                )
            )

        return {"ticker": ticker, "history": history}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Valuation history query error: {e}"
        )
