import re
import pandas as pd
from typing import Any, Optional
from src.dashboard.utils import db

def extract_year_int(yr_val: Any) -> Optional[int]:
    """
    Extracts 4-digit calendar year integer from year string.
    E.g. 'Mar 2024' -> 2024, 'TTM' -> None, '2023' -> 2023.
    """
    if not yr_val:
        return None
    val_str = str(yr_val).strip()
    if val_str.upper() == "TTM":
        return None
    match = re.search(r"\b(19\d\d|20\d\d)\b", val_str)
    return int(match.group(1)) if match else None

def map_year_to_price_date(year_str: str) -> Optional[str]:
    """
    Maps financial year strings to stock price date strings.
    E.g. "Mar 2024" -> "2024-03-01", "Dec 2012" -> "2012-12-01".
    """
    if not year_str:
        return None
    months = {
        "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
        "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
    }
    match = re.search(r"\b([A-Za-z]{3})\s+(\d{4})\b", str(year_str).strip())
    if match:
        m = match.group(1).upper()
        y = match.group(2)
        m_num = months.get(m)
        if m_num:
            return f"{y}-{m_num}-01"
    return None

def get_master_data() -> pd.DataFrame:
    """
    Combines cached dataframes from db.py into a single master dataframe,
    calculates PE, PB dynamically, and returns the merged result.
    """
    df_ratios = db.get_ratios()
    df_companies = db.get_companies()
    df_sectors = db.get_sectors()
    df_pl = db.get_pl()
    df_prices = db.get_valuation()
    
    # 1. Join ratios with companies and sectors
    df = pd.merge(df_ratios, df_companies[['id', 'company_name']], left_on='company_id', right_on='id', how='left')
    df = pd.merge(df, df_sectors[['company_id', 'broad_sector', 'sub_sector']], on='company_id', how='left')
    
    # Rename broad_sector to sector for convenience
    df = df.rename(columns={'broad_sector': 'sector'})
    
    # 2. Join with P&L to get net_profit and sales
    df = pd.merge(df, df_pl[['company_id', 'year', 'sales', 'net_profit']], on=['company_id', 'year'], how='left')
    
    # 3. Map year to price date and merge with stock prices
    df['price_date'] = df['year'].apply(map_year_to_price_date)
    df = pd.merge(df, df_prices[['company_id', 'date', 'close_price']], left_on=['company_id', 'price_date'], right_on=['company_id', 'date'], how='left')
    
    # 4. Calculate PE and PB dynamically
    def safe_div(num, denom):
        if pd.isnull(num) or pd.isnull(denom) or denom <= 0:
            return None
        return round(num / denom, 2)
        
    df['pe'] = df.apply(lambda r: safe_div(r.get('close_price'), r.get('earnings_per_share')), axis=1)
    df['pb'] = df.apply(lambda r: safe_div(r.get('close_price'), r.get('book_value_per_share')), axis=1)
    
    # 5. Extract calendar year integer
    df['year_int'] = df['year'].apply(extract_year_int)
    
    return df
