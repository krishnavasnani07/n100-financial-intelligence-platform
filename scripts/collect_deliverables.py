import os
import shutil
from pathlib import Path

def copy_file(src, dest):
    src_path = Path(src)
    dest_path = Path(dest)
    if src_path.exists():
        try:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_path)
            print(f"  [+] Copied: {src_path} -> {dest_path}")
            return True
        except Exception as e:
            print(f"  [-] Failed to copy {src_path}: {e}")
            return False
    else:
        print(f"  [!] Missing source file: {src_path}")
        return False

def copy_dir(src, dest):
    src_path = Path(src)
    dest_path = Path(dest)
    if src_path.exists() and src_path.is_dir():
        try:
            if dest_path.exists():
                shutil.rmtree(dest_path)
            shutil.copytree(src_path, dest_path)
            print(f"  [+] Copied Directory: {src_path} -> {dest_path}")
            return True
        except Exception as e:
            print(f"  [-] Failed to copy directory {src_path}: {e}")
            return False
    else:
        print(f"  [!] Missing source directory: {src_path}")
        return False

def main():
    dest_dir = "output/final_deliverables"
    os.makedirs(dest_dir, exist_ok=True)
    
    print(f"Archiving all 23 project deliverables to {dest_dir}...\n")
    
    # Track success of each deliverable (D-01 to D-23)
    results = {}
    
    # D-01: Database File
    results["D-01"] = copy_file("db/nifty100.db", f"{dest_dir}/nifty100.db")
    
    # D-02: Load Audit CSV
    results["D-02"] = copy_file("output/audit/load_audit.csv", f"{dest_dir}/load_audit.csv")
    
    # D-03: Validation Failures CSV
    results["D-03"] = copy_file("output/validation/validation_failures.csv", f"{dest_dir}/validation_failures.csv")
    
    # D-04: Exploratory Queries SQL
    results["D-04"] = copy_file("notebooks/exploratory_queries.sql", f"{dest_dir}/exploratory_queries.sql")
    
    # D-05: Financial Ratios Table (inside nifty100.db, adding CAGR validation csv as backup verification)
    results["D-05"] = copy_file("output/cagr_validation_report.csv", f"{dest_dir}/cagr_validation_report.csv")
    
    # D-06: Capital Allocation CSV
    results["D-06"] = copy_file("output/capital_allocation_summary.csv", f"{dest_dir}/capital_allocation_summary.csv")
    
    # D-07: Screener Output Excel
    results["D-07"] = copy_file("output/screener_output.xlsx", f"{dest_dir}/screener_output.xlsx")
    
    # D-08: Screener Config YAML
    results["D-08"] = copy_file("config/screener_config.yaml", f"{dest_dir}/screener_config.yaml")
    
    # D-09: Peer Comparison Excel
    results["D-09"] = copy_file("output/peer_comparison.xlsx", f"{dest_dir}/peer_comparison.xlsx")
    
    # D-10: Sprint 3 92 Radar Charts (Directory)
    results["D-10"] = copy_dir("reports/radar_charts", f"{dest_dir}/radar_charts")
    
    # D-11: Streamlit Dashboard (app.py)
    results["D-11"] = copy_file("app.py", f"{dest_dir}/app.py")
    
    # D-12: Valuation Summary Excel
    results["D-12"] = copy_file("output/valuation_summary.xlsx", f"{dest_dir}/valuation_summary.xlsx")
    
    # D-13: Cashflow Intelligence Excel
    results["D-13"] = copy_file("output/cashflow_intelligence.xlsx", f"{dest_dir}/cashflow_intelligence.xlsx")
    
    # D-14: Pros & Cons Generated
    results["D-14"] = copy_file("output/pros_cons_generated.csv", f"{dest_dir}/pros_cons_generated.csv")
    
    # D-15: Parsed Text Analytics
    results["D-15"] = copy_file("output/analysis_parsed.csv", f"{dest_dir}/analysis_parsed.csv")
    
    # D-16: 92 Company Tearsheets (Directory)
    results["D-16"] = copy_dir("reports/tearsheets", f"{dest_dir}/tearsheets")
    
    # D-17: 11 Sector Reports (Directory)
    results["D-17"] = copy_dir("reports/sector", f"{dest_dir}/sector")
    
    # D-18: Portfolio Summary PDF
    results["D-18"] = copy_file("reports/portfolio/portfolio_summary.pdf", f"{dest_dir}/portfolio_summary.pdf")
    
    # D-19: Cluster Labels CSV
    results["D-19"] = copy_file("output/cluster_labels.csv", f"{dest_dir}/cluster_labels.csv")
    
    # D-20: FastAPI Server (src/api/main.py)
    results["D-20"] = copy_file("src/api/main.py", f"{dest_dir}/api_main.py")
    
    # D-21: Pytest HTML Report
    results["D-21"] = copy_file("reports/pytest_report.html", f"{dest_dir}/pytest_report.html")
    
    # D-22: Analyst Operations Guide
    results["D-22"] = copy_file("docs/analyst_guide.pdf", f"{dest_dir}/analyst_guide.pdf")
    
    # D-23: Acceptance Checklist PDF
    results["D-23"] = copy_file("docs/acceptance_checklist.pdf", f"{dest_dir}/acceptance_checklist.pdf")
    
    success_count = sum(1 for val in results.values() if val)
    print(f"\nArchiving completed. {success_count}/{len(results)} deliverables successfully collected.")

if __name__ == "__main__":
    main()
