import os
import shutil

def main():
    dest_dir = "output/final_deliverables"
    os.makedirs(dest_dir, exist_ok=True)
    
    # Define the core deliverables
    deliverables = [
        # Analytics & Machine Learning Outputs
        ("output/cluster_labels.csv", "cluster_labels.csv"),
        ("reports/elbow_plot.png", "elbow_plot.png"),
        ("reports/profitability_distribution.png", "profitability_distribution.png"),
        ("output/portfolio_stats.csv", "portfolio_stats.csv"),
        ("output/valuation_flags.csv", "valuation_flags.csv"),
        
        # API Schemas & Documentation
        ("docs/openapi.json", "openapi.json"),
        ("docs/analyst_guide.pdf", "analyst_guide.pdf"),
        
        # Test Suite Quality Reports
        ("reports/pytest_report.html", "pytest_report.html"),
        
        # Structured Excel Modeling Deliverables
        ("output/peer_comparison.xlsx", "peer_comparison.xlsx"),
        ("output/screener_output.xlsx", "screener_output.xlsx"),
        ("output/valuation_summary.xlsx", "valuation_summary.xlsx"),
        ("output/cashflow_intelligence.xlsx", "cashflow_intelligence.xlsx"),
        
        # Comprehensive Sector Booklets
        ("output/peer_report.pdf", "peer_report.pdf"),
        
        # Ingestion & Data Quality Audits
        ("output/validation/validation_failures.csv", "validation_failures.csv"),
        ("output/validation/validation_summary.csv", "validation_summary.csv"),
        ("output/validation/validation_log.txt", "validation_log.txt"),
        
        # Pipeline Audits & Logs
        ("output/cagr_validation_report.csv", "cagr_validation_report.csv"),
        ("output/capital_allocation_summary.csv", "capital_allocation_summary.csv"),
        ("output/distress_alerts.csv", "distress_alerts.csv"),
        ("output/pattern_changes.csv", "pattern_changes.csv"),
        ("output/pros_cons_generated.csv", "pros_cons_generated.csv"),
        ("output/report_generation_summary.csv", "report_generation_summary.csv"),
        ("output/skipped_tearsheets.csv", "skipped_tearsheets.csv"),
        ("output/analysis_parsed.csv", "analysis_parsed.csv"),
        ("output/parse_failures.csv", "parse_failures.csv"),
        
        # Strategy Rankings
        ("output/csv/rankings.csv", "rankings.csv")
    ]
    
    print(f"Archiving deliverables to {dest_dir}...")
    success_count = 0
    
    for src, name in deliverables:
        dest_path = os.path.join(dest_dir, name)
        if os.path.exists(src):
            try:
                shutil.copy2(src, dest_path)
                print(f"  [+] Copied: {src} -> {dest_path}")
                success_count += 1
            except Exception as e:
                print(f"  [-] Failed to copy {src}: {e}")
        else:
            print(f"  [!] Missing source file: {src}")
            
    print(f"\nArchiving completed. {success_count}/{len(deliverables)} deliverables successfully collected.")

if __name__ == "__main__":
    main()
