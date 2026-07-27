import sqlite3
import pandas as pd
import re

from src.screener.presets import (
    screen_quality_compounder,
    screen_value_pick,
    screen_growth_accelerator,
    screen_dividend_champion,
    screen_debt_free_blue_chip,
    screen_turnaround_watch
)
from src.analytics.ratios import calculate_icr_label
from src.analytics.cagr import calculate_cagr

def map_year_to_price_date(year_str):
    if not year_str:
        return None
    months = {
        "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
        "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
    }
    match = re.search(r"([A-Za-z]{3})\s+(\d{4})", str(year_str))
    if match:
        m = match.group(1).upper()
        y = match.group(2)
        m_num = months.get(m)
        if m_num:
            return f"{y}-{m_num}-01"
    return None

def extract_year_int(yr_val):
    if str(yr_val).strip().upper() == "TTM":
        return None
    m = re.search(r"\b(19\d\d|20\d\d)\b", str(yr_val))
    return int(m.group(1)) if m else None

conn = sqlite3.connect("db/nifty100.db")

# Load financial_ratios
df_ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
df_sectors = pd.read_sql_query("SELECT company_id, broad_sector as sector FROM sectors", conn)
df_pl = pd.read_sql_query("SELECT company_id, year, sales, interest FROM profitandloss", conn)

df = pd.merge(df_ratios, df_sectors, on="company_id", how="left")
df = pd.merge(df, df_pl, on=["company_id", "year"], how="left")

# Map price date
df["price_date"] = df["year"].apply(map_year_to_price_date)

# Load stock_prices
df_prices = pd.read_sql_query("SELECT company_id, date as price_date, close_price FROM stock_prices", conn)

# Merge
df = pd.merge(df, df_prices, on=["company_id", "price_date"], how="left")

# Calculate pe and pb
def safe_div(num, denom):
    if num is None or denom is None or denom <= 0:
        return None
    return round(num / denom, 2)

df["pe"] = df.apply(lambda r: safe_div(r.get("close_price"), r.get("earnings_per_share")), axis=1)
df["pb"] = df.apply(lambda r: safe_div(r.get("close_price"), r.get("book_value_per_share")), axis=1)

# Calculate dividend_yield
def calc_div_yield(row):
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
    axis=1
)

df["year_int"] = df["year"].apply(extract_year_int)
df = df.dropna(subset=["year_int"]).sort_values(by=["company_id", "year_int"])

df["prev_de"] = df.groupby("company_id")["debt_to_equity"].shift(1)
df["de_declining_yoy"] = df.apply(lambda r: r.get("debt_to_equity") is not None and r.get("prev_de") is not None and float(r.get("debt_to_equity")) < float(r.get("prev_de")), axis=1)

# 3Y Revenue CAGR
df["sales_3y_ago"] = df.groupby("company_id")["sales"].shift(3)
def row_cagr_3y(row):
    start = row.get("sales_3y_ago")
    end = row.get("sales")
    if pd.isnull(start) or pd.isnull(end):
        return None
    val, flag = calculate_cagr(start, end, 3)
    return val if flag == "VALID" else None
df["revenue_cagr_3yr"] = df.apply(row_cagr_3y, axis=1)

# Keep latest year
df_latest = df.sort_values(by="year_int", ascending=False).drop_duplicates(subset=["company_id"], keep="first").copy()

print("Quality Compounder:", len(screen_quality_compounder(df_latest)))
print("Value Pick:", len(screen_value_pick(df_latest)))
print("Growth Accelerator:", len(screen_growth_accelerator(df_latest)))
print("Dividend Champion:", len(screen_dividend_champion(df_latest)))
print("Debt-Free Blue Chip:", len(screen_debt_free_blue_chip(df_latest)))
print("Turnaround Watch:", len(screen_turnaround_watch(df_latest)))

conn.close()
