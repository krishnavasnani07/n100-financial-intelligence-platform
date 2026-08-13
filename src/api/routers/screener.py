from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from src.api.database import clean_df_nans
from src.config.settings import DB_PATH

router = APIRouter(tags=["Screener"])


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
