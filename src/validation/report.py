import csv
import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from src.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Rule:
    id: str
    name: str
    severity: str  # 'CRITICAL' or 'WARNING'
    description: str


@dataclass
class ValidationFailure:
    rule_id: str
    severity: str  # 'CRITICAL' or 'WARNING'
    table: str
    company_id: str
    year: str
    field: str
    raw_value: Any
    issue: str
    timestamp: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_row(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "table": self.table,
            "company_id": self.company_id,
            "year": self.year,
            "field": self.field,
            "raw_value": str(self.raw_value) if self.raw_value is not None else "",
            "issue": self.issue,
            "timestamp": self.timestamp,
        }


@dataclass
class ValidationResult:
    passed: bool
    rule_id: str
    total_checked: int
    warnings_count: int
    errors_count: int
    execution_time_sec: float
    failures: List[ValidationFailure]


class ValidationReport:
    def __init__(self):
        self.failures: List[ValidationFailure] = []
        self.rules_checked: Dict[str, int] = {}

    def add_failure(self, failure: ValidationFailure):
        self.failures.append(failure)
        # Log to application log as well
        log_msg = f"{failure.severity} - {failure.rule_id} - {failure.issue} on table {failure.table}, company {failure.company_id}, year {failure.year}, field {failure.field}, value {failure.raw_value}"
        if failure.severity == "CRITICAL":
            logger.error(log_msg)
        else:
            logger.warning(log_msg)

    def register_check(self, rule_id: str, count: int = 1):
        if rule_id not in self.rules_checked:
            self.rules_checked[rule_id] = 0
        self.rules_checked[rule_id] += count

    def save(self, output_dir: Path = None):
        if output_dir is None:
            output_dir = settings.VALIDATION_DIR

        output_dir.mkdir(parents=True, exist_ok=True)

        failures_file = output_dir / "validation_failures.csv"
        summary_file = output_dir / "validation_summary.csv"
        log_file = output_dir / "validation_log.txt"

        # 1. Save validation_failures.csv
        fieldnames = [
            "rule_id",
            "severity",
            "table",
            "company_id",
            "year",
            "field",
            "raw_value",
            "issue",
            "timestamp",
        ]
        try:
            with open(failures_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for failure in self.failures:
                    writer.writerow(failure.to_row())
            logger.info(f"Saved validation failures to {failures_file}")
        except Exception as e:
            logger.error(f"Failed to write validation failures to CSV: {e}")

        # 2. Save validation_summary.csv
        # Calculate summary per rule
        rule_failures = {}
        for failure in self.failures:
            rule_failures[failure.rule_id] = rule_failures.get(failure.rule_id, 0) + 1

        try:
            from src.validation.dq_rules import RULE_REGISTRY

            with open(summary_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["rule_id", "rule_name", "severity", "passed", "failed"]
                )
                # We want to cover all 16 rules from DQ-01 to DQ-16
                for i in range(1, 17):
                    rule_id = f"DQ-{i:02d}"
                    failures_count = rule_failures.get(rule_id, 0)
                    total_checked = self.rules_checked.get(rule_id, 0)
                    passed_count = max(0, total_checked - failures_count)
                    rule_meta = RULE_REGISTRY.get(rule_id)
                    rule_name = rule_meta.name if rule_meta else rule_id
                    severity = rule_meta.severity if rule_meta else "UNKNOWN"
                    writer.writerow(
                        [rule_id, rule_name, severity, passed_count, failures_count]
                    )
            logger.info(f"Saved validation summary to {summary_file}")
        except Exception as e:
            logger.error(f"Failed to write validation summary to CSV: {e}")

        # 3. Save validation_log.txt
        try:
            with open(log_file, mode="w", encoding="utf-8") as f:
                f.write(
                    f"Validation Log - Run completed at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write("=" * 80 + "\n")
                f.write(f"Total failures detected: {len(self.failures)}\n")
                critical_count = sum(
                    1 for x in self.failures if x.severity == "CRITICAL"
                )
                warning_count = sum(1 for x in self.failures if x.severity == "WARNING")
                f.write(f"CRITICAL Failures: {critical_count}\n")
                f.write(f"WARNING Failures: {warning_count}\n\n")

                f.write("Summary per rule:\n")
                for i in range(1, 17):
                    rule_id = f"DQ-{i:02d}"
                    failures_count = rule_failures.get(rule_id, 0)
                    f.write(f"  {rule_id}: {failures_count} failures\n")

                f.write("\nDetailed Failures:\n")
                f.write("-" * 80 + "\n")
                for failure in self.failures:
                    f.write(
                        f"[{failure.timestamp}] {failure.severity} - {failure.rule_id} in {failure.table}: {failure.issue}\n"
                    )
                    f.write(
                        f"  Company: {failure.company_id} | Year: {failure.year} | Field: {failure.field} | Raw Value: {failure.raw_value}\n"
                    )
            logger.info(f"Saved validation log to {log_file}")
        except Exception as e:
            logger.error(f"Failed to write validation log file: {e}")
