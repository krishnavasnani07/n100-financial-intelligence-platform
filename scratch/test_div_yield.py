import sqlite3
import pandas as pd
import re

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

# Filter latest year
df["year_int"] = df["year"].apply(extract_year_int)
df = df.dropna(subset=["year_int"]).sort_values(by=["company_id", "year_int"])

# Keep latest year
df_latest = df.sort_values(by="year_int", ascending=False).drop_duplicates(subset=["company_id"], keep="first").copy()

print("Dividend Yield Stats:")
print(df_latest["dividend_yield"].describe())

# Check how many would pass Dividend Champion:
# min_dividend_yield = 2.0, max_dividend_payout = 80.0, min_fcf = 0.0
df_div = df_latest[
    (df_latest["dividend_yield"] >= 2.0) & 
    (df_latest["dividend_payout_ratio_pct"] <= 80.0) & 
    (df_latest["free_cash_flow_cr"] >= 0.0)
]
print("Dividend Champion Count with real yield:", len(df_div))
print(df_div[["company_id", "dividend_yield", "dividend_payout_ratio_pct", "free_cash_flow_cr"]])

conn.close()
