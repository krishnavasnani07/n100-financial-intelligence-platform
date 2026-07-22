from pathlib import Path

from src.analytics.ratio_validation import categorize_ratio_mismatch, write_ratio_edge_case_log


def test_classify_source_issue_for_unrealistic_percentage():
    category, reason = categorize_ratio_mismatch("ROE", 42.7, 0.52)

    assert category == "DATA_SOURCE_ISSUE"
    assert "source" in reason.lower() or "malformed" in reason.lower()


def test_classify_version_difference_for_small_delta():
    category, reason = categorize_ratio_mismatch("ROCE", 14.1, 12.7)

    assert category == "VERSION_DIFFERENCE"
    assert "minor" in reason.lower() or "close" in reason.lower()


def test_write_ratio_edge_case_log(tmp_path: Path):
    entries = [
        {
            "company_id": "TCS",
            "ratio_name": "ROE",
            "computed": 42.7,
            "source": 0.52,
            "difference": 42.18,
            "category": "DATA_SOURCE_ISSUE",
            "reason": "Source value appears malformed for a percentage-based ratio.",
        }
    ]

    output_path = write_ratio_edge_case_log(entries, output_path=tmp_path / "ratio_edge_cases.log")

    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "ROE Mismatch" in content
    assert "DATA_SOURCE_ISSUE" in content
