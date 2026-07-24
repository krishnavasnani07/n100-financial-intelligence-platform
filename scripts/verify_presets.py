"""
Validation script for Sprint 3 Day 16 Preset Screeners.
Runs each of the 6 presets, verifies count constraints (5-50), and exports to CSV.
"""

import sys
from pathlib import Path
import pandas as pd

# Add root folder to sys.path to ensure src imports work
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.config.settings import OUTPUT_DIR
from src.screener.presets import load_screener_master_data, run_preset


def main():
    print("==================================================")
    print("Running Sprint 3 Day 16 Preset Screener Verification")
    print("==================================================")

    # 1. Load Master Data
    print("Loading enriched screening master dataset...")
    master_df = load_screener_master_data()
    print(f"Total unique companies loaded: {len(master_df)}")
    print("--------------------------------------------------")

    presets = [
        ("Quality Compounder", "quality_compounder.csv"),
        ("Value Pick", "value_pick.csv"),
        ("Growth Accelerator", "growth_accelerator.csv"),
        ("Dividend Champion", "dividend_champion.csv"),
        ("Debt-Free Blue Chip", "debt_free_bluechip.csv"),
        ("Turnaround Watch", "turnaround_watch.csv")
    ]

    all_passed = True
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, filename in presets:
        print(f"Executing Screener: '{name}'...")
        try:
            df_res = run_preset(name, master_df)
            count = len(df_res)
            
            # Export to CSV
            out_path = OUTPUT_DIR / filename
            df_res.to_csv(out_path, index=False)
            
            # Print info
            print(f"  -> Returned {count} companies.")
            print(f"  -> Exported to: {out_path}")
            
            # Print sample tickers
            sample_tickers = list(df_res["company_id"].head(5))
            print(f"  -> Sample tickers: {sample_tickers}")
            
            # Check constraint (5 to 50 companies)
            if 5 <= count <= 50:
                print(f"  -> [PASS] Company count ({count}) is within the 5-50 range.")
            else:
                print(f"  -> [FAIL] Company count ({count}) is OUTSIDE the 5-50 range!")
                all_passed = False
                
        except Exception as e:
            print(f"  -> [ERROR] Failed to run preset '{name}': {e}")
            all_passed = False
        print("--------------------------------------------------")

    if all_passed:
        print("SUCCESS: All preset screeners passed the business validations!")
        sys.exit(0)
    else:
        print("FAILURE: One or more preset screeners failed validation.")
        sys.exit(1)


if __name__ == "__main__":
    main()
