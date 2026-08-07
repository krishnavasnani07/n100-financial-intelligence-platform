"""
Confidence and filtering engine for financial insights.
Determines if insights meet the target confidence thresholds (>60%).
"""

from typing import Any, Dict, List

# Minimum confidence percentage required to export an insight
MIN_CONFIDENCE_THRESHOLD = 60.0


def score_sector_adjustment(base_score: float, rule_id: str, sector: str) -> float:
    """
    Applies optional sector-specific weights to the confidence score.
    For example, high debt rules have less confidence/priority for Financials.
    """
    score = base_score

    # Financial sector specific adjustments
    if sector == "Financials":
        # Financials naturally have low ICR or high leverage; reduce confidence for debt alerts
        if rule_id in ["CON-01", "CON-06", "CON-11"]:
            score *= 0.7
        # High ROE is very strong in Financials
        elif rule_id == "PRO-01":
            score = min(100.0, score * 1.1)

    return round(score, 2)


def filter_insights(insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filters out any insights that fall below the minimum confidence threshold (60%)."""
    return [
        insight
        for insight in insights
        if insight.get("confidence_pct", 0.0) >= MIN_CONFIDENCE_THRESHOLD
    ]
