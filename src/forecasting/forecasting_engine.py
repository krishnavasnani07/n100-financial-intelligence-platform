"""
Financial Forecasting Engine.
Uses linear regression (NumPy) and moving averages to project company
Revenue and EPS for the next 3 years based on historical profit and loss records.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from src.config.settings import DB_PATH
from src.peer_analysis.comparison import extract_year_int


def load_historical_pl(company_id: str, db_path: Path | None = None) -> pd.DataFrame:
    """
    Loads historical sales (Revenue) and EPS for a company.
    """
    db_file = db_path or DB_PATH
    conn = sqlite3.connect(str(db_file))

    query = """
    SELECT year, sales, eps 
    FROM profitandloss 
    WHERE company_id = ?
    """
    df = pd.read_sql_query(query, conn, params=[company_id])
    conn.close()

    if df.empty:
        return pd.DataFrame(columns=["year_int", "sales", "eps"])

    df["year_int"] = df["year"].apply(extract_year_int)
    # Drop rows without valid year integer or missing metrics
    df = (
        df.dropna(subset=["year_int"]).sort_values(by="year_int").reset_index(drop=True)
    )
    return df


def forecast_metric(
    years: np.ndarray, values: np.ndarray, forecast_years_ahead: int = 3
) -> tuple[np.ndarray, np.ndarray, float, float]:
    """
    Applies linear regression and moving average to project values.

    Returns:
        Tuple of (forecast_years, regression_forecasts, moving_avg_forecast, growth_rate)
    """
    n = len(years)
    if n < 2:
        # Fallback if too few data points
        next_years = (
            np.arange(years[-1] + 1, years[-1] + 1 + forecast_years_ahead)
            if n > 0
            else np.array([2025, 2026, 2027])
        )
        last_val = values[-1] if n > 0 else 100.0
        return next_years, np.array([last_val] * forecast_years_ahead), last_val, 0.0

    # Fit linear regression: y = m * x + c
    slope, intercept = np.polyfit(years, values, 1)

    next_years = np.arange(years[-1] + 1, years[-1] + 1 + forecast_years_ahead)
    reg_forecasts = slope * next_years + intercept

    # Calculate simple annual growth rate of the fit
    base_val = slope * years[-1] + intercept
    growth_rate = (slope / base_val * 100.0) if base_val != 0 else 0.0

    # Moving average (last 3-year average as constant forecast)
    ma_val = float(values[-3:].mean()) if n >= 3 else float(values.mean())

    return next_years, reg_forecasts.round(2), round(ma_val, 2), round(growth_rate, 2)


def generate_company_forecasts(
    company_id: str, db_path: Path | None = None
) -> dict[str, any]:
    """
    Generates 3-year forecasts for Sales (Revenue) and EPS.
    """
    df = load_historical_pl(company_id, db_path)

    if len(df) < 2:
        return {
            "success": False,
            "message": f"Insufficient historical data for company {company_id}",
        }

    years = df["year_int"].values
    sales = df["sales"].values
    eps = df["eps"].values

    fc_years, sales_reg, sales_ma, sales_growth = forecast_metric(years, sales)
    _, eps_reg, eps_ma, eps_growth = forecast_metric(years, eps)

    # Prepare historical records for UI
    historical = []
    for idx, row in df.iterrows():
        historical.append(
            {
                "Year": int(row["year_int"]),
                "Revenue": float(row["sales"]),
                "EPS": float(row["eps"]),
            }
        )

    # Prepare forecast records
    forecasts = []
    for i, yr in enumerate(fc_years):
        forecasts.append(
            {
                "Year": int(yr),
                "Revenue (Linear Regression)": float(sales_reg[i]),
                "Revenue (Moving Average)": float(sales_ma),
                "EPS (Linear Regression)": float(eps_reg[i]),
                "EPS (Moving Average)": float(eps_ma),
            }
        )

    return {
        "success": True,
        "company_id": company_id,
        "historical": historical,
        "forecasts": forecasts,
        "revenue_trend_growth_rate": sales_growth,
        "eps_trend_growth_rate": eps_growth,
    }
