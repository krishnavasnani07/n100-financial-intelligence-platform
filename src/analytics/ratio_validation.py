from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


def categorize_ratio_mismatch(ratio_name: str, computed: Optional[float], source: Optional[float]) -> Tuple[str, str]:
    """Categorize a ratio mismatch based on the magnitude and plausibility of the difference."""
    if computed is None or source is None:
        return "DATA_SOURCE_ISSUE", "Missing values prevent a meaningful comparison."

    try:
        diff = abs(float(computed) - float(source))
    except (TypeError, ValueError):
        return "DATA_SOURCE_ISSUE", "Source or computed value is malformed."

    if math.isnan(diff):
        return "DATA_SOURCE_ISSUE", "Encountered a non-numeric comparison value."

    if source == 0:
        return "DATA_SOURCE_ISSUE", "Source value is zero, which is not plausible for this ratio."

    if abs(float(source)) < 1 and abs(float(computed)) > 10:
        return "DATA_SOURCE_ISSUE", "Source value appears malformed for a percentage-based ratio."

    if diff <= 5.0:
        return "VERSION_DIFFERENCE", "Difference is small and consistent with a minor version/source change."

    return "FORMULA_DISCREPANCY", "Difference is too large to be a simple version mismatch."


def build_ratio_mismatch_entries(
    computed_df: pd.DataFrame,
    source_df: pd.DataFrame,
    ratio_name: str,
    computed_column: str,
    source_column: str,
    company_id_column: str = "company_id",
) -> List[Dict[str, Any]]:
    """Build mismatch rows for a ratio by comparing computed values against source values."""
    merged = pd.merge(
        computed_df[[company_id_column, computed_column]].rename(columns={computed_column: "computed"}),
        source_df[[company_id_column, source_column]].rename(columns={source_column: "source"}),
        on=company_id_column,
        how="inner",
    )

    entries: List[Dict[str, Any]] = []
    for row in merged.itertuples(index=False):
        computed = getattr(row, "computed")
        source = getattr(row, "source")
        if pd.isna(computed) and pd.isna(source):
            continue
        if pd.isna(computed) or pd.isna(source):
            category, reason = "DATA_SOURCE_ISSUE", "Missing values prevent a meaningful comparison."
        else:
            category, reason = categorize_ratio_mismatch(ratio_name, float(computed), float(source))

        diff = abs(float(computed) - float(source)) if not pd.isna(computed) and not pd.isna(source) else None
        entries.append(
            {
                "company_id": getattr(row, company_id_column),
                "ratio_name": ratio_name,
                "computed": computed,
                "source": source,
                "difference": diff,
                "category": category,
                "reason": reason,
            }
        )

    return entries


def write_ratio_edge_case_log(entries: List[Dict[str, Any]], output_path: Optional[Path | str] = None) -> Path:
    """Persist ratio edge case entries to the requested log file."""
    out_path = Path(output_path or Path("output") / "ratio_edge_cases.log")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    existing_content = out_path.read_text(encoding="utf-8") if out_path.exists() else ""
    blocks: List[str] = []
    for entry in entries:
        block = "\n".join(
            [
                "===================================",
                f"{entry['ratio_name']} Mismatch",
                f"Company : {entry['company_id']}",
                f"Computed : {entry['computed']}",
                f"Source : {entry['source']}",
                f"Difference : {entry['difference']}",
                f"Category : {entry['category']}",
                f"Reason : {entry['reason']}",
                "===================================",
            ]
        )
        if block not in existing_content:
            blocks.append(block)

    if blocks:
        if existing_content.strip():
            combined = existing_content.rstrip() + "\n\n" + "\n\n".join(blocks) + "\n"
        else:
            combined = "\n\n".join(blocks) + "\n"
        out_path.write_text(combined, encoding="utf-8")

    return out_path
