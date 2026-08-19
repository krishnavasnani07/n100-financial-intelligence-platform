import sqlite3

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.api.database import clean_df_nans, clean_dict_nans
from src.config.settings import DB_PATH, OUTPUT_DIR
from src.reports.report_utils import map_sector
from src.screener.ranking import calculate_rankings
from src.visualization.radar_chart import (
    calculate_normalized_metrics,
    load_universe_data,
)

router = APIRouter(tags=["Peers"])


def get_companies_map() -> dict[str, str]:
    """Get companies map."""
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute("SELECT id, company_name FROM companies").fetchall()
        return {r[0]: r[1] for r in rows}
    except Exception:
        return {}
    finally:
        conn.close()


def compute_global_percentiles(
    df: pd.DataFrame, columns_config: dict[str, bool]
) -> pd.DataFrame:
    """Compute global percentiles."""
    df_pct = df.copy()
    for col, lower_is_better in columns_config.items():
        series = df[col].dropna()
        if series.empty:
            df_pct[f"{col}_percentile"] = 50.0
            continue
        ascending = not lower_is_better
        ranks = df[col].rank(ascending=ascending, method="min")
        min_rank = ranks.min()
        max_rank = ranks.max()
        if max_rank > min_rank:
            df_pct[f"{col}_percentile"] = (
                100.0 * (ranks - min_rank) / (max_rank - min_rank)
            ).round(2)
        else:
            df_pct[f"{col}_percentile"] = 100.0
    return df_pct


@router.get("/peer")
def get_peer_comparison(
    sector: str | None = Query(None, description="Sector name to filter peers")
):
    """
    Legacy route to return peer comparisons, top performers, and sector statistics.
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


@router.get("/peers/{group_name}")
def get_peer_group(group_name: str):
    """
    Returns all companies in that peer group along with their percentile ranks for the 10 KPIs.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT company_id, is_benchmark FROM peer_groups WHERE LOWER(peer_group_name) = LOWER(?)",
            [group_name],
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Peer group '{group_name}' has no records or does not exist.",
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

        # 10 KPIs to compute percentiles for
        METRICS_10 = {
            "return_on_equity_pct": False,
            "return_on_capital_employed_pct": False,
            "net_profit_margin_pct": False,
            "operating_profit_margin_pct": False,
            "debt_to_equity": True,
            "interest_coverage": False,
            "free_cash_flow_cr": False,
            "revenue_cagr_5yr": False,
            "pat_cagr_5yr": False,
            "composite_quality_score": False,
        }

        # Calculate percentiles across the whole universe first
        df_pct = compute_global_percentiles(df, METRICS_10)

        group_company_ids = [r[0] for r in rows]
        df_group = df_pct[df_pct["company_id"].isin(group_company_ids)]

        companies_map = get_companies_map()
        results = []
        for _, row in df_group.iterrows():
            cid = str(row["company_id"])
            is_bench = next((r[1] for r in rows if r[0] == cid), 0)

            results.append(
                clean_dict_nans(
                    {
                        "company_id": cid,
                        "company_name": companies_map.get(cid, ""),
                        "ticker": cid,
                        "is_benchmark": bool(is_bench),
                        "sector": row["sector_standardized"],
                        "metrics": {
                            "roe_pct": row["return_on_equity_pct"],
                            "roce_pct": row["return_on_capital_employed_pct"],
                            "net_profit_margin_pct": row["net_profit_margin_pct"],
                            "operating_profit_margin_pct": row[
                                "operating_profit_margin_pct"
                            ],
                            "debt_to_equity": row["debt_to_equity"],
                            "interest_coverage": row["interest_coverage"],
                            "free_cash_flow_cr": row["free_cash_flow_cr"],
                            "revenue_cagr_5yr": row["revenue_cagr_5yr"],
                            "pat_cagr_5yr": row["pat_cagr_5yr"],
                            "composite_quality_score": row["composite_quality_score"],
                        },
                        "percentiles": {
                            "roe_pct": row["return_on_equity_pct_percentile"],
                            "roce_pct": row[
                                "return_on_capital_employed_pct_percentile"
                            ],
                            "net_profit_margin_pct": row[
                                "net_profit_margin_pct_percentile"
                            ],
                            "operating_profit_margin_pct": row[
                                "operating_profit_margin_pct_percentile"
                            ],
                            "debt_to_equity": row["debt_to_equity_percentile"],
                            "interest_coverage": row["interest_coverage_percentile"],
                            "free_cash_flow_cr": row["free_cash_flow_cr_percentile"],
                            "revenue_cagr_5yr": row["revenue_cagr_5yr_percentile"],
                            "pat_cagr_5yr": row["pat_cagr_5yr_percentile"],
                            "composite_quality_score": row[
                                "composite_quality_score_percentile"
                            ],
                        },
                    }
                )
            )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Peers query error: {e}")


@router.get("/companies/{ticker}/peers/compare")
def compare_peers(ticker: str):
    """
    Returns radar-chart-ready comparison data across 8 axes/metrics.
    """
    ticker = ticker.strip().upper()

    conn = sqlite3.connect(DB_PATH)
    try:
        row_group = conn.execute(
            "SELECT peer_group_name FROM peer_groups WHERE UPPER(company_id) = ?",
            [ticker],
        ).fetchone()
        if not row_group:
            raise HTTPException(
                status_code=404, detail=f"Peer group not found for company '{ticker}'"
            )

        group_name = row_group[0]

        row_bench = conn.execute(
            "SELECT company_id FROM peer_groups WHERE peer_group_name = ? AND is_benchmark = 1",
            [group_name],
        ).fetchone()
        if not row_bench:
            raise HTTPException(
                status_code=404,
                detail=f"Benchmark company not found for peer group '{group_name}'",
            )

        benchmark_ticker = row_bench[0]
    finally:
        conn.close()

    try:
        df_raw = load_universe_data(DB_PATH)
        df_norm = calculate_normalized_metrics(df_raw)

        if ticker not in df_raw["company_id"].values:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker}' not found in financial data",
            )
        if benchmark_ticker not in df_raw["company_id"].values:
            raise HTTPException(
                status_code=404,
                detail=f"Benchmark company '{benchmark_ticker}' not found in financial data",
            )

        row_target_raw = df_raw[df_raw["company_id"] == ticker].iloc[0]
        row_target_norm = df_norm[df_norm["company_id"] == ticker].iloc[0]

        row_bench_raw = df_raw[df_raw["company_id"] == benchmark_ticker].iloc[0]
        row_bench_norm = df_norm[df_norm["company_id"] == benchmark_ticker].iloc[0]

        axes = [
            "roe",
            "roce",
            "revenue_cagr",
            "pat_cagr",
            "operating_margin",
            "current_ratio",
            "debt_to_equity",
            "composite_score",
        ]

        return clean_dict_nans(
            {
                "axes": axes,
                "company": {
                    "ticker": ticker,
                    "normalized": {ax: float(row_target_norm[ax]) for ax in axes},
                    "raw": {
                        ax: (
                            float(row_target_raw[ax])
                            if pd.notnull(row_target_raw[ax])
                            else None
                        )
                        for ax in axes
                    },
                },
                "benchmark": {
                    "ticker": benchmark_ticker,
                    "normalized": {ax: float(row_bench_norm[ax]) for ax in axes},
                    "raw": {
                        ax: (
                            float(row_bench_raw[ax])
                            if pd.notnull(row_bench_raw[ax])
                            else None
                        )
                        for ax in axes
                    },
                },
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {e}")
