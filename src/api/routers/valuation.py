from fastapi import APIRouter, HTTPException

from src.api.database import clean_df_nans
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
