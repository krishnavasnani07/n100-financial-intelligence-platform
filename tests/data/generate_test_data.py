from pathlib import Path

import pandas as pd

# Create tests/data directory
data_dir = Path("tests/data")
data_dir.mkdir(parents=True, exist_ok=True)


def save_mock_excel(filename: str, sheet: str, df: pd.DataFrame, title: str):
    file_path = data_dir / filename
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        # Write title at row 0
        pd.DataFrame([[title]]).to_excel(
            writer, sheet_name=sheet, startrow=0, header=False, index=False
        )
        # Write data starting at row 1
        df.to_excel(writer, sheet_name=sheet, startrow=1, index=False)


# 1. Duplicate company IDs (companies table)
df_dup_comp = pd.DataFrame(
    [
        {"id": "ABB", "name": "ABB India Ltd"},
        {"id": "TCS", "name": "Tata Consultancy Services Ltd"},
        {"id": "ABB", "name": "Duplicate ABB Ltd"},
    ]
)
save_mock_excel("duplicate_company.xlsx", "Companies", df_dup_comp, "Companies Master")

# 2. Invalid year formats
df_inv_year = pd.DataFrame(
    [
        {"company_id": "ABB", "year": "2023-03"},
        {"company_id": "ABB", "year": "TTM"},
        {"company_id": "TCS", "year": "Mar 2016 9m"},
        {"company_id": "TCS", "year": "Mar-23"},
    ]
)
save_mock_excel(
    "invalid_year.xlsx", "Profit & Loss", df_inv_year, "Profit & Loss Master"
)

# 3. Invalid tickers
df_inv_ticker = pd.DataFrame(
    [
        {"id": "ABB", "name": "ABB"},
        {"id": "A", "name": "Too Short Ticker"},
        {"id": "TCS_INVALID_LONG", "name": "Too Long Ticker"},
        {"id": "TCS.NS", "name": "Contains Invalid Character"},
    ]
)
save_mock_excel("invalid_ticker.xlsx", "Companies", df_inv_ticker, "Companies Master")

# 4. Negative sales
df_neg_sales = pd.DataFrame(
    [
        {"company_id": "ABB", "year": "2023-03", "sales": 1000.0},
        {"company_id": "TCS", "year": "2023-03", "sales": -50.0},
    ]
)
save_mock_excel(
    "negative_sales.xlsx", "Profit & Loss", df_neg_sales, "Profit & Loss Master"
)

# 5. Balance sheet mismatches
df_bs_mismatch = pd.DataFrame(
    [
        {
            "company_id": "ABB",
            "year": "2023-03",
            "total_assets": 100.0,
            "total_liabilities": 100.0,
        },
        {
            "company_id": "TCS",
            "year": "2023-03",
            "total_assets": 150.0,
            "total_liabilities": 120.0,
        },
    ]
)
save_mock_excel(
    "balancesheet_mismatch.xlsx",
    "Balance Sheet",
    df_bs_mismatch,
    "Balance Sheet Master",
)

print("Mock test data files generated successfully under tests/data/")
