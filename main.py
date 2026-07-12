import sys
from src.validation.validator import DataValidator
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
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
        
        if summary['success']:
            print("Validation Completed Successfully\n")
        else:
            print("Validation Failed with CRITICAL Errors\n")
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Validation pipeline execution failed: {e}", exc_info=True)
        print(f"\n[x] CRITICAL PIPELINE ERROR: {e}\n")
        sys.exit(2)


if __name__ == "__main__":
    main()