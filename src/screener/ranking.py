"""
Scoring and Ranking Engine for Nifty 100 Financial Intelligence Platform.
Computes sector-relative winsorized, normalized composite quality scores and ranks companies.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from src.analytics.cagr import calculate_cagr
from src.analytics.ratios import calculate_icr_label
from src.config.constants import (QUALITY_SCORE_WEIGHTS, WINSOR_LOWER_QUANTILE,
                                  WINSOR_UPPER_QUANTILE)
from src.config.settings import DB_PATH, OUTPUT_DIR
from src.utils.helpers import extract_year_int, map_year_to_price_date


def load_ranking_master_data(db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads all historical financial ratios joined with sector, sales, interest, and net profit.
    This preserves multi-year history to compute 5-year FCF CAGR and other historical metrics.

    Parameters:
        db_path (Optional[Path]): Path to the SQLite database.

    Returns:
        pd.DataFrame: Loaded master ratios and financial data.
    """
    db_file = db_path or DB_PATH
    conn = sqlite3.connect(db_file)
    try:
        # Join financial_ratios with sectors (for sector) and profitandloss (for sales, net_profit, and interest)
        query = """
        SELECT 
            fr.*,
            s.broad_sector as sector,
            s.sub_sector,
            s.index_weight_pct,
            pl.sales as sales,
            pl.interest as interest,
            pl.net_profit as net_profit
        FROM financial_ratios fr
        LEFT JOIN sectors s ON fr.company_id = s.company_id
        LEFT JOIN profitandloss pl ON fr.company_id = pl.company_id AND fr.year = pl.year
        """
        df = pd.read_sql_query(query, conn)

        # Load stock prices to compute P/E and P/B dynamically
        query_prices = (
            "SELECT company_id, date as price_date, close_price FROM stock_prices"
        )
        df_prices = pd.read_sql_query(query_prices, conn)
    finally:
        conn.close()

    df["price_date"] = df["year"].apply(map_year_to_price_date)
    df = pd.merge(df, df_prices, on=["company_id", "price_date"], how="left")

    # Compute P/E and P/B dynamically
    def safe_div(num: Any, denom: Any) -> Optional[float]:
        try:
            n = float(num)
            d = float(denom)
            if d <= 0 or pd.isnull(n) or pd.isnull(d):
                return None
            return round(n / d, 2)
        except (ValueError, TypeError):
            return None

    df["pe"] = df.apply(
        lambda r: safe_div(r.get("close_price"), r.get("earnings_per_share")), axis=1
    )
    df["pb"] = df.apply(
        lambda r: safe_div(r.get("close_price"), r.get("book_value_per_share")), axis=1
    )

    # Compute dividend_yield dynamically
    def calc_div_yield(row: pd.Series) -> float:
        payout = row.get("dividend_payout_ratio_pct")
        eps = row.get("earnings_per_share")
        price = row.get("close_price")
        if payout is None or eps is None or price is None or price <= 0:
            return 0.0
        return round((payout * eps) / price, 2)

    df["dividend_yield"] = df.apply(calc_div_yield, axis=1)

    # Compute icr_label
    df["icr_label"] = df.apply(
        lambda r: calculate_icr_label(r.get("interest"), r.get("interest_coverage")),
        axis=1,
    )

    # Parse calendar years and sort
    df["year_int"] = df["year"].apply(extract_year_int)
    df = (
        df.dropna(subset=["year_int"]).sort_values(by=["company_id", "year_int"]).copy()
    )

    # Historical calculations (YoY Debt and 3Y Revenue CAGR)
    df["prev_de"] = df.groupby("company_id")["debt_to_equity"].shift(1)

    def is_de_declining(row: pd.Series) -> bool:
        cur = row.get("debt_to_equity")
        prev = row.get("prev_de")
        if cur is None or prev is None or pd.isnull(cur) or pd.isnull(prev):
            return False
        return float(cur) < float(prev)

    df["de_declining_yoy"] = df.apply(is_de_declining, axis=1)

    df["sales_3y_ago"] = df.groupby("company_id")["sales"].shift(3)

    def row_cagr_3y(row: pd.Series) -> Optional[float]:
        start = row.get("sales_3y_ago")
        end = row.get("sales")
        if pd.isnull(start) or pd.isnull(end) or start is None or end is None:
            return None
        val, flag = calculate_cagr(
            start,
            end,
            3,
            company_id=str(row.get("company_id")),
            metric_name="Revenue_3Y",
        )
        return val if flag == "VALID" else None

    df["revenue_cagr_3yr"] = df.apply(row_cagr_3y, axis=1)

    return df


def winsorize_and_scale(series: pd.Series, lower_is_better: bool = False) -> pd.Series:
    """
    Normalise a series using P10/P90 winsorisation and Min-Max scaling to 0-100.
    Missing values (NaN/None) are filled with the median of non-null values in the series.

    Parameters:
        series (pd.Series): The series of numeric values to scale.
        lower_is_better (bool): True if lower values represent better performance.

    Returns:
        pd.Series: Normalized and scaled score series (0 to 100).
    """
    non_null = series.dropna()
    if non_null.empty:
        return pd.Series(0.0, index=series.index)

    p10 = non_null.quantile(WINSOR_LOWER_QUANTILE)
    p90 = non_null.quantile(WINSOR_UPPER_QUANTILE)
    median_val = non_null.median()

    # Fill NaN values with median
    filled = series.fillna(median_val)

    # Winsorize: Cap values at P10 and P90
    if p90 > p10:
        capped = filled.clip(lower=p10, upper=p90)
        if lower_is_better:
            scores = 100.0 * (p90 - capped) / (p90 - p10)
        else:
            scores = 100.0 * (capped - p10) / (p90 - p10)
    else:
        # If P10 == P90, all companies have the same value.
        # If that value is negative/zero (e.g. FCF positive flag), they get 0. Otherwise, 100.
        if p10 <= 0:
            scores = pd.Series(0.0, index=series.index)
        else:
            scores = pd.Series(100.0, index=series.index)

    return scores


def calculate_rankings(db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Main function to compute composite quality scores and overall ranks.
    Saves scores to SQLite and returns the ranked DataFrame for the latest year.

    Parameters:
        db_path (Optional[Path]): Path to the SQLite database.

    Returns:
        pd.DataFrame: Sorted, ranked DataFrame containing computed composite scores and ranks.
    """
    db_file = db_path or DB_PATH
    df = load_ranking_master_data(db_file)

    # 1. Compute 5-year FCF CAGR dynamically
    # Build lookup map: (company_id, year_int) -> free_cash_flow_cr
    fcf_lookup = {}
    for _, row in df.iterrows():
        cid = str(row["company_id"])
        yint = row["year_int"]
        if pd.notnull(yint):
            fcf_lookup[(cid, int(yint))] = row.get("free_cash_flow_cr")

    fcf_cagr_vals = []
    for _, row in df.iterrows():
        cid = str(row["company_id"])
        yint = row["year_int"]
        fcf_latest = row.get("free_cash_flow_cr")
        fcf_5yr_ago = fcf_lookup.get((cid, yint - 5)) if pd.notnull(yint) else None

        cagr_val, flag = calculate_cagr(
            fcf_5yr_ago, fcf_latest, 5, company_id=cid, metric_name="FCF_5Y"
        )
        fcf_cagr_vals.append(cagr_val if flag == "VALID" else None)

    df["fcf_cagr_5yr"] = fcf_cagr_vals

    # 2. Compute CFO/PAT ratio dynamically
    def calc_cfo_pat(row: pd.Series) -> Optional[float]:
        cfo = row.get("cash_from_operations_cr")
        pat = row.get("net_profit")
        if cfo is None or pat is None or pd.isnull(cfo) or pd.isnull(pat) or pat <= 0:
            return None
        return round(cfo / pat, 4)

    df["cfo_pat_ratio"] = df.apply(calc_cfo_pat, axis=1)

    # 3. Compute FCF Positive Flag dynamically
    def calc_fcf_flag(row: pd.Series) -> float:
        fcf = row.get("free_cash_flow_cr")
        if fcf is None or pd.isnull(fcf):
            return 0.0
        return 1.0 if fcf > 0 else 0.0

    df["fcf_positive"] = df.apply(calc_fcf_flag, axis=1)

    # Keep only the latest year for each company
    df_latest = (
        df.sort_values(by="year_int", ascending=False)
        .drop_duplicates(subset=["company_id"], keep="first")
        .copy()
    )

    # 4. Sector-relative normalization (Winsorisation and scaling)
    # Define metrics: (column_name, lower_is_better)
    metrics_config = {
        "roe": ("return_on_equity_pct", False),
        "roce": ("return_on_capital_employed_pct", False),
        "npm": ("net_profit_margin_pct", False),
        "fcf_cagr": ("fcf_cagr_5yr", False),
        "cfo_pat": ("cfo_pat_ratio", False),
        "fcf_flag": ("fcf_positive", False),
        "rev_cagr": ("revenue_cagr_5yr", False),
        "pat_cagr": ("pat_cagr_5yr", False),
        "de": ("debt_to_equity", True),
        "icr": ("interest_coverage", False),
    }

    # Initialize score columns
    df_scored = df_latest.copy()
    for name in metrics_config:
        df_scored[f"{name}_score"] = 0.0

    # Normalise within each sector
    for sector, group in df_scored.groupby("sector"):
        for name, (col, lower_is_better) in metrics_config.items():
            series = group[col]
            scores = winsorize_and_scale(series, lower_is_better)
            df_scored.loc[group.index, f"{name}_score"] = scores

    # Post-process: Handle "Debt Free" companies for Interest Coverage and Debt-to-Equity
    for idx, row in df_scored.iterrows():
        label = str(row.get("icr_label", "")).strip().lower()
        if label == "debt free" or row.get("debt_to_equity") == 0:
            df_scored.at[idx, "icr_score"] = 100.0
            df_scored.at[idx, "de_score"] = 100.0

    comp_score = pd.Series(0.0, index=df_scored.index)
    for col, weight in QUALITY_SCORE_WEIGHTS.items():
        comp_score += df_scored[col] * weight

    df_scored["composite_quality_score"] = comp_score.round(2)

    # 6. Rank companies descending by composite quality score
    df_scored = df_scored.sort_values(
        by="composite_quality_score", ascending=False
    ).reset_index(drop=True)
    df_scored["overall_rank"] = (
        df_scored["composite_quality_score"]
        .rank(method="dense", ascending=False)
        .astype(int)
    )

    # 7. Update composite_quality_score in the SQLite database financial_ratios table
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    try:
        update_data = []
        for _, row in df_scored.iterrows():
            cid = row["company_id"]
            yr = row["year"]
            score = row["composite_quality_score"]
            update_data.append((score, cid, yr))

        cursor.executemany(
            "UPDATE financial_ratios SET composite_quality_score = ? WHERE company_id = ? AND year = ?",
            update_data,
        )
        conn.commit()
    finally:
        conn.close()

    # 8. Export rankings to output/csv/rankings.csv
    csv_dir = OUTPUT_DIR / "csv"
    csv_dir.mkdir(parents=True, exist_ok=True)
    df_scored.to_csv(csv_dir / "rankings.csv", index=False)

    return df_scored


if __name__ == "__main__":
    calculate_rankings()
