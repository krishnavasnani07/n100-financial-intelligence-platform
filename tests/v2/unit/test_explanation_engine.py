from __future__ import annotations

from pathlib import Path

import pytest

from tests.v2.unit.test_repositories import test_db_path
from src.analytics.explanation.explanation_engine import ExplanationEngine


def test_dupont_roe_explanation(test_db_path: Path):
    engine = ExplanationEngine(db_path=test_db_path)
    
    # Calculate TCS ROE Change between Mar 2023 and Mar 2024
    res = engine.explain_roe_change("TCS", "Mar 2023", "Mar 2024")
    
    assert res["company_id"] == "TCS"
    assert res["year_1"] == "Mar 2023"
    assert res["year_2"] == "Mar 2024"
    assert res["roe_1"] > 0
    assert res["roe_2"] > 0
    assert res["roe_change"] == round(res["roe_2"] - res["roe_1"], 2)
    
    # Verify additivity: sum of contributions equals change
    attribs = res["contributions"]
    sum_attribs = attribs["operating_efficiency_npm"] + attribs["asset_efficiency_ato"] + attribs["financial_leverage_fl"]
    assert abs(sum_attribs - res["roe_change"]) < 0.1
    
    # Verify primary driver is populated
    assert res["primary_driver"] in [
        "Operating Efficiency (NPM)",
        "Asset Use Efficiency (ATO)",
        "Financial Leverage (FL)"
    ]
    assert res["explanation"] is not None


def test_quality_score_explanation(test_db_path: Path):
    engine = ExplanationEngine(db_path=test_db_path)
    
    # Explain INFY quality score changes
    res = engine.explain_quality_score_change("INFY", "Mar 2023", "Mar 2024")
    
    assert res["company_id"] == "INFY"
    assert res["score_1"] == 84.2
    assert res["score_2"] == 86.8
    assert res["score_change"] == 2.6
    
    # Verify drivers are computed
    assert len(res["drivers"]) == 7
    assert "ROE" in res["drivers"]
    assert "ROCE" in res["drivers"]
    assert res["explanation"] is not None


def test_peer_relative_explanation(test_db_path: Path):
    engine = ExplanationEngine(db_path=test_db_path)
    
    # Generate relative check for TCS in Mar 2024
    res = engine.generate_peer_relative_explanation("TCS", "Mar 2024")
    
    assert res["company_id"] == "TCS"
    assert res["year"] == "Mar 2024"
    assert res["sector"] == "IT"
    assert res["metrics"]["company_roe"] == 48.2
    assert res["metrics"]["sector_median_roe"] == 39.95
    assert "premium profitability" in res["explanation"]
