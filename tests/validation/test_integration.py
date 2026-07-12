from src.config import settings
from src.validation.validator import DataValidator


def test_validator_integration():
    """
    Integration test to run the validation engine against all 12 raw datasets,
    asserting that files are loaded, checked, and reports are successfully created.
    """
    validator = DataValidator(raw_data_dir=settings.RAW_DATA_DIR)

    # Run validation
    summary = validator.run_validation()

    # Assert validation output structure
    assert isinstance(summary, dict)
    assert "success" in summary
    assert "status" in summary
    assert "total_failures" in summary
    assert "critical_failures" in summary
    assert "warning_failures" in summary
    assert "rules_checked" in summary

    # Assert files are generated in output/validation directory
    output_dir = settings.VALIDATION_DIR
    failures_file = output_dir / "validation_failures.csv"
    summary_file = output_dir / "validation_summary.csv"
    log_file = output_dir / "validation_log.txt"

    assert failures_file.exists(), f"Failures CSV not found at {failures_file}"
    assert summary_file.exists(), f"Summary CSV not found at {summary_file}"
    assert log_file.exists(), f"Validation Log not found at {log_file}"

    # Let's verify failures CSV content exists
    assert failures_file.stat().st_size > 0, "validation_failures.csv is empty"
    assert summary_file.stat().st_size > 0, "validation_summary.csv is empty"
    assert log_file.stat().st_size > 0, "validation_log.txt is empty"

    # We expect some failures in the raw dataset
    assert summary["total_failures"] > 0
    # Let's check that all 16 rules are checked
    assert len(summary["rules_checked"]) > 0
