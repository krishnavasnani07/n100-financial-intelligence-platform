import sys
import time
from src.validation.validator import DataValidator
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    start_pipeline_time = time.time()
    print("=" * 80)
    print("          NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM - DATA VALIDATION          ")
    print("=" * 80)
    
    try:
        validator = DataValidator()
        summary = validator.run_validation()
        
        # Calculate failures per rule from validator report
        rule_failures = {}
        for failure in validator.report.failures:
            rule_failures[failure.rule_id] = rule_failures.get(failure.rule_id, 0) + 1

        print("\n==============================")
        print("VALIDATION SUMMARY")
        print("==============================\n")

        critical_rules = {"DQ-01", "DQ-02", "DQ-03", "DQ-07", "DQ-08"}

        for i in range(1, 17):
            rule_id = f"DQ-{i:02d}"
            failures_count = rule_failures.get(rule_id, 0)
            if failures_count == 0:
                status = "PASS"
            elif rule_id in critical_rules:
                status = f"FAIL ({failures_count})"
            else:
                status = f"WARNING ({failures_count})"
            
            print(f"{rule_id} {status}\n")

        print("------------------------------")
        print(f"Total Errors : {summary['critical_failures']}")
        print(f"Warnings : {summary['warning_failures']}")
        print("------------------------------\n")
        
        print("==============================")
        print("SQLITE DATABASE LOADING")
        print("==============================\n")
        
        from src.database.loader import DatabaseLoader
        from src.database.queries import check_foreign_key_violations, get_table_counts

        db_loader = DatabaseLoader()
        load_summary = db_loader.load_all(validator.datasets)

        print(f"[+] Data loaded successfully into SQLite!")
        print(f"    Rows Inserted : {load_summary['total_inserted']}")
        print(f"    Rows Rejected : {load_summary['total_rejected']}")
        print(f"    Audit Report  : {load_summary['audit_file']}")
        print(f"    Backup DB     : {load_summary['backup_file']}\n")

        print("--- Verification Check ---")
        fk_violations = check_foreign_key_violations()
        print(f"Foreign Key Violations: {len(fk_violations)}")
        
        table_counts = get_table_counts()
        print("\nTable Record Counts:")
        for tbl, count in table_counts.items():
            print(f"  {tbl:<20}: {count}")
        print("------------------------------\n")

        total_pipeline_runtime = round(time.time() - start_pipeline_time, 2)

        print("==============================")
        print("PROFITABILITY KPI RATIO ENGINE")
        print("==============================\n")
        
        import sqlite3
        import pandas as pd
        from src.analytics.ratios import ProfitabilityEngine
        from src.config.settings import BASE_DIR

        db_path = BASE_DIR / "db" / "nifty100.db"
        conn = sqlite3.connect(db_path)

        query = """
            SELECT 
                c.id AS company_id,
                s.broad_sector,
                pl.year,
                pl.sales,
                pl.operating_profit,
                pl.opm_percentage AS reported_opm,
                pl.net_profit,
                bs.equity_capital,
                bs.reserves,
                bs.borrowings,
                bs.total_assets
            FROM companies c
            LEFT JOIN sectors s ON c.id = s.company_id
            JOIN profitandloss pl ON c.id = pl.company_id
            JOIN balancesheet bs ON c.id = bs.company_id AND pl.year = bs.year
        """
        df_ratios_data = pd.read_sql(query, conn)
        conn.close()

        all_ratio_results = []
        for idx, row in df_ratios_data.iterrows():
            is_fin = str(row.get("broad_sector")) == "Financials"
            results = ProfitabilityEngine.compute_period_ratios(
                company_id=row["company_id"],
                year=row["year"],
                sales=row["sales"],
                operating_profit=row["operating_profit"],
                net_profit=row["net_profit"],
                equity_capital=row["equity_capital"],
                reserves=row["reserves"],
                borrowings=row["borrowings"],
                total_assets=row["total_assets"],
                reported_opm=row["reported_opm"],
                is_financial=is_fin
            )
            all_ratio_results.extend(results)

        ProfitabilityEngine.export_ratio_audit_and_summary(all_ratio_results)
        print(f"[+] Computed profitability ratios for {len(df_ratios_data)} period records!")
        print(f"    Itemized Ratio Audit Log : output/ratio_calculation_log.csv")
        print(f"    KPI Summary Statistics   : output/ratio_summary.csv\n")

        # Print Phase 14 Execution Summary Dashboard
        print("====================================")
        print("      ETL EXECUTION SUMMARY         ")
        print("====================================")
        print(f"Files Processed      : {len(validator.datasets)}")
        print(f"Tables Loaded        : {load_summary['tables_loaded']}")
        print(f"Rows Read            : {load_summary['total_read']}")
        print(f"Rows Inserted        : {load_summary['total_inserted']}")
        print(f"Rows Rejected        : {load_summary['total_rejected']}")
        print(f"KPI Ratios Evaluated : {len(all_ratio_results)}")
        print("")
        print(f"Validation Errors    : {summary['critical_failures']}")
        print(f"FK Violations        : {len(fk_violations)}")
        print("")
        print(f"Total Runtime        : {total_pipeline_runtime} sec")
        print("")
        print("Database Status      : SUCCESS")
        print("====================================\n")

        if not summary['success']:
            print("Validation completed with warnings / critical findings logged to audit CSVs.\n")
            
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}", exc_info=True)
        print(f"\n[x] CRITICAL PIPELINE ERROR: {e}\n")
        sys.exit(2)


if __name__ == "__main__":
    main()