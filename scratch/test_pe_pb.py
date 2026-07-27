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

conn = sqlite3.connect("db/nifty100.db")

# Load financial_ratios
df_ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)

# Map price date
df_ratios["price_date"] = df_ratios["year"].apply(map_year_to_price_date)

# Load stock_prices
df_prices = pd.read_sql_query("SELECT company_id, date as price_date, close_price FROM stock_prices", conn)

# Merge
df_merged = pd.merge(df_ratios, df_prices, on=["company_id", "price_date"], how="left")

# Calculate pe and pb
def safe_div(num, denom):
    if num is None or denom is None or denom <= 0:
        return None
    return round(num / denom, 2)

df_merged["pe"] = df_merged.apply(lambda r: safe_div(r.get("close_price"), r.get("earnings_per_share")), axis=1)
df_merged["pb"] = df_merged.apply(lambda r: safe_div(r.get("close_price"), r.get("book_value_per_share")), axis=1)

print("Merged rows:", len(df_merged))
print("Matched prices count:", df_merged["close_price"].notnull().sum())
print("P/E calculated count:", df_merged["pe"].notnull().sum())
print("P/B calculated count:", df_merged["pb"].notnull().sum())

print("\nSample calculated values:")
print(df_merged[["company_id", "year", "close_price", "earnings_per_share", "pe", "book_value_per_share", "pb"]].dropna().head(10))

conn.close()
