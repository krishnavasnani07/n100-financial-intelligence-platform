from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from src.api.database import clean_df_nans
from src.config.settings import DB_PATH

router = APIRouter(tags=["Peers"])


@router.get("/peer")
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

        if sector and isinstance(sector, str):
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
