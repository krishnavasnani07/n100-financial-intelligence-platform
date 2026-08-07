import pandas as pd

from src.dashboard.utils import db
from src.utils.helpers import extract_year_int, map_year_to_price_date


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
    df = pd.merge(
        df_ratios,
        df_companies[["id", "company_name"]],
        left_on="company_id",
        right_on="id",
        how="left",
    )
    df = pd.merge(
        df,
        df_sectors[["company_id", "broad_sector", "sub_sector"]],
        on="company_id",
        how="left",
    )

    # Rename broad_sector to sector for convenience
    df = df.rename(columns={"broad_sector": "sector"})

    # 2. Join with P&L to get net_profit and sales
    df = pd.merge(
        df,
        df_pl[["company_id", "year", "sales", "net_profit"]],
        on=["company_id", "year"],
        how="left",
    )

    # 3. Map year to price date and merge with stock prices
    df["price_date"] = df["year"].apply(map_year_to_price_date)
    df = pd.merge(
        df,
        df_prices[["company_id", "date", "close_price"]],
        left_on=["company_id", "price_date"],
        right_on=["company_id", "date"],
        how="left",
    )

    # 4. Calculate PE and PB dynamically
    def safe_div(num, denom):
        if pd.isnull(num) or pd.isnull(denom) or denom <= 0:
            return None
        return round(num / denom, 2)

    df["pe"] = df.apply(
        lambda r: safe_div(r.get("close_price"), r.get("earnings_per_share")), axis=1
    )
    df["pb"] = df.apply(
        lambda r: safe_div(r.get("close_price"), r.get("book_value_per_share")), axis=1
    )

    # 5. Extract calendar year integer
    df["year_int"] = df["year"].apply(extract_year_int)

    return df
