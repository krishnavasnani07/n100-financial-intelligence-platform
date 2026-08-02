"""
Unit tests for the Financial Intelligence Pros & Cons generator.
Verifies rules logic, registry structure, confidence adjustments, and fallback generation.
"""

import pytest
from unittest.mock import MagicMock

from src.nlp.rules import RULES_REGISTRY, get_avg_val, FinancialRule
from src.nlp.confidence import score_sector_adjustment, filter_insights


def test_rules_registry_integrity():
    """Verify that the registry contains exactly 24 rules (12 PRO and 12 CON)."""
    assert len(RULES_REGISTRY) == 24
    
    pro_rules = [r for r in RULES_REGISTRY if r.rule_type == "PRO"]
    con_rules = [r for r in RULES_REGISTRY if r.rule_type == "CON"]
    
    assert len(pro_rules) == 12
    assert len(con_rules) == 12
    
    # Check rule IDs are unique
    rule_ids = [r.rule_id for r in RULES_REGISTRY]
    assert len(rule_ids) == len(set(rule_ids))


def test_get_avg_val_helper():
    """Test the get_avg_val helper function."""
    history = [{"val": 10}, {"val": 20}, {"val": None}]
    assert get_avg_val(history, "val") == 15.0
    assert get_avg_val([], "val", default=5.0) == 5.0


def test_pro_01_consistently_high_roe():
    """Test PRO-01 (ROE > 20% for 3 years) logic."""
    pro_01_rule = next(r for r in RULES_REGISTRY if r.rule_id == "PRO-01")
    
    # High ROE history
    history_pass = [
        {"return_on_equity_pct": 21.0},
        {"return_on_equity_pct": 25.0},
        {"return_on_equity_pct": 22.0}
    ]
    res = pro_01_rule.evaluate(history_pass, "IT")
    assert res is not None
    assert res["rule_id"] == "PRO-01"
    assert res["type"] == "PRO"
    assert res["confidence_pct"] >= 65.0
    
    # Failing history
    history_fail = [
        {"return_on_equity_pct": 19.0},
        {"return_on_equity_pct": 25.0},
        {"return_on_equity_pct": 22.0}
    ]
    assert pro_01_rule.evaluate(history_fail, "IT") is None


def test_pro_03_debt_free():
    """Test PRO-03 (Debt to equity = 0) logic."""
    pro_03_rule = next(r for r in RULES_REGISTRY if r.rule_id == "PRO-03")
    
    # Debt-free
    history_pass = [{"debt_to_equity": 0.0}]
    res = pro_03_rule.evaluate(history_pass, "Consumer Goods")
    assert res is not None
    assert res["confidence_pct"] == 95.0
    
    # Non-debt-free
    history_fail = [{"debt_to_equity": 0.5}]
    assert pro_03_rule.evaluate(history_fail, "Consumer Goods") is None


def test_con_01_elevated_debt():
    """Test CON-01 (Debt to equity > 2 on non-financial company)."""
    con_01_rule = next(r for r in RULES_REGISTRY if r.rule_id == "CON-01")
    
    # Elevated debt non-financial
    history = [{"debt_to_equity": 2.5}]
    res = con_01_rule.evaluate(history, "Automobile")
    assert res is not None
    assert res["rule_id"] == "CON-01"
    
    # Financial company should not trigger this rule
    assert con_01_rule.evaluate(history, "Financials") is None


def test_sector_adjustments():
    """Test sector adjustment logic."""
    # CON-01 on financials should reduce score
    score_fin = score_sector_adjustment(80.0, "CON-01", "Financials")
    assert score_fin == 56.0  # 80 * 0.7 = 56.0
    
    # PRO-01 on financials should boost score
    score_roe = score_sector_adjustment(70.0, "PRO-01", "Financials")
    assert score_roe == 77.0  # 70 * 1.1 = 77.0


def test_filter_insights():
    """Test filtering by confidence threshold."""
    insights = [
        {"rule_id": "PRO-01", "confidence_pct": 59.0},
        {"rule_id": "PRO-02", "confidence_pct": 61.0},
        {"rule_id": "CON-01", "confidence_pct": 60.0}
    ]
    filtered = filter_insights(insights)
    assert len(filtered) == 2
    assert all(x["confidence_pct"] >= 60.0 for x in filtered)
