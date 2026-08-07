"""
Financial rules registry for the automatic Pros & Cons generator.
Defines 12 Pro rules and 12 Con rules to analyze company financial status.
"""

from typing import Any, Callable, Dict, List, Optional


class FinancialRule:
    """
    Represents a financial analysis rule.
    Evaluates historical data and assigns a confidence score.
    """

    def __init__(
        self,
        rule_id: str,
        rule_type: str,
        condition: Callable[[List[Dict[str, Any]], str], bool],
        message: str,
        confidence_fn: Callable[[List[Dict[str, Any]], str], float],
    ):
        self.rule_id = rule_id
        self.rule_type = rule_type
        self.condition = condition
        self.message = message
        self.confidence_fn = confidence_fn

    def evaluate(
        self, history: List[Dict[str, Any]], sector: str
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates the rule against the historical records (sorted ASC by year) and sector.
        Returns the parsed insight or None if condition is not met.
        """
        if not history:
            return None
        try:
            if self.condition(history, sector):
                score = self.confidence_fn(history, sector)
                score = max(0.0, min(100.0, float(score)))
                return {
                    "rule_id": self.rule_id,
                    "type": self.rule_type,
                    "text": self.message,
                    "confidence_pct": round(score, 2),
                }
        except Exception:
            # Return None if evaluation fails to avoid pipeline crash
            pass
        return None


# Helper function to compute average of a column safely
def get_avg_val(history: List[Dict[str, Any]], key: str, default: float = 0.0) -> float:
    vals = [r.get(key) for r in history if r.get(key) is not None]
    return sum(vals) / len(vals) if vals else default


# Define the rule registry list
RULES_REGISTRY: List[FinancialRule] = []


def register_rule(rule_id: str, rule_type: str, message: str):
    """Decorator to register rules easily."""

    def decorator(funcs: tuple[Callable, Callable]):
        cond_fn, conf_fn = funcs
        RULES_REGISTRY.append(
            FinancialRule(rule_id, rule_type, cond_fn, message, conf_fn)
        )
        return funcs

    return decorator


# =====================================================================
# PRO RULES (PRO-01 to PRO-12)
# =====================================================================


# PRO-01: Consistently High ROE (>20% for last 3 years)
def pro_01_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return len(history) >= 3 and all(
        r.get("return_on_equity_pct") is not None and r["return_on_equity_pct"] > 20.0
        for r in history[-3:]
    )


def pro_01_conf(history: List[Dict[str, Any]], sector: str) -> float:
    avg_roe = get_avg_val(history[-3:], "return_on_equity_pct", 20.0)
    return 65.0 + (avg_roe - 20.0) * 2.0


register_rule(
    "PRO-01",
    "PRO",
    "Consistently high return on equity above 20% demonstrates exceptional capital efficiency.",
)((pro_01_cond, pro_01_conf))


# PRO-02: Strong Free Cash Flow (>0 for last 5 years)
def pro_02_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    check_len = min(5, len(history))
    return check_len >= 3 and all(
        r.get("free_cash_flow_cr") is not None and r["free_cash_flow_cr"] > 0.0
        for r in history[-check_len:]
    )


def pro_02_conf(history: List[Dict[str, Any]], sector: str) -> float:
    check_len = min(5, len(history))
    avg_conv = get_avg_val(history[-check_len:], "fcf_conversion", 1.0)
    return 70.0 + min(max(0.0, avg_conv * 10), 25.0)


register_rule(
    "PRO-02",
    "PRO",
    "Strong free cash flow generation over 5 years signals healthy business fundamentals.",
)((pro_02_cond, pro_02_conf))


# PRO-03: Debt-Free Balance Sheet (Debt to Equity = 0)
def pro_03_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 1
        and history[-1].get("debt_to_equity") is not None
        and history[-1]["debt_to_equity"] == 0.0
    )


def pro_03_conf(history: List[Dict[str, Any]], sector: str) -> float:
    return 95.0 if sector != "Financials" else 85.0


register_rule(
    "PRO-03",
    "PRO",
    "Debt-free balance sheet provides financial flexibility and eliminates interest burden.",
)((pro_03_cond, pro_03_conf))


# PRO-04: Robust Revenue Growth (>15% 5Y CAGR)
def pro_04_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 1
        and history[-1].get("revenue_cagr_5yr") is not None
        and history[-1]["revenue_cagr_5yr"] > 15.0
    )


def pro_04_conf(history: List[Dict[str, Any]], sector: str) -> float:
    cagr = history[-1]["revenue_cagr_5yr"]
    return 70.0 + (cagr - 15.0) * 1.3


register_rule(
    "PRO-04",
    "PRO",
    "Robust revenue growth demonstrates strong market demand and business expansion.",
)((pro_04_cond, pro_04_conf))


# PRO-05: High Operating Margin (>20% in latest year)
def pro_05_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 1
        and history[-1].get("operating_profit_margin_pct") is not None
        and history[-1]["operating_profit_margin_pct"] > 20.0
    )


def pro_05_conf(history: List[Dict[str, Any]], sector: str) -> float:
    opm = history[-1]["operating_profit_margin_pct"]
    return 65.0 + (opm - 20.0) * 1.2


register_rule(
    "PRO-05",
    "PRO",
    "High operating profit margins indicate strong pricing power and cost efficiency.",
)((pro_05_cond, pro_05_conf))


# PRO-06: Strong PAT Growth (>15% 5Y CAGR)
def pro_06_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 1
        and history[-1].get("pat_cagr_5yr") is not None
        and history[-1]["pat_cagr_5yr"] > 15.0
    )


def pro_06_conf(history: List[Dict[str, Any]], sector: str) -> float:
    cagr = history[-1]["pat_cagr_5yr"]
    return 70.0 + (cagr - 15.0) * 1.25


register_rule(
    "PRO-06", "PRO", "Strong profit growth indicates robust bottom-line performance."
)((pro_06_cond, pro_06_conf))


# PRO-07: High Interest Coverage (ICR > 5, non-financials)
def pro_07_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 1
        and sector != "Financials"
        and history[-1].get("interest_coverage") is not None
        and history[-1]["interest_coverage"] > 5.0
    )


def pro_07_conf(history: List[Dict[str, Any]], sector: str) -> float:
    icr = history[-1]["interest_coverage"]
    return 70.0 + min(icr, 25.0)


register_rule(
    "PRO-07",
    "PRO",
    "High interest coverage ratio indicates comfortable debt servicing capability.",
)((pro_07_cond, pro_07_conf))


# PRO-08: Attractive Dividend Yield (>2%)
def pro_08_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 1
        and history[-1].get("dividend_yield_pct") is not None
        and history[-1]["dividend_yield_pct"] > 2.0
    )


def pro_08_conf(history: List[Dict[str, Any]], sector: str) -> float:
    dy = history[-1]["dividend_yield_pct"]
    return 70.0 + (dy - 2.0) * 5.0


register_rule(
    "PRO-08",
    "PRO",
    "Attractive dividend yield provides stable cash returns to shareholders.",
)((pro_08_cond, pro_08_conf))


# PRO-09: EPS CAGR (>15%)
def pro_09_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 1
        and history[-1].get("eps_cagr_5yr") is not None
        and history[-1]["eps_cagr_5yr"] > 15.0
    )


def pro_09_conf(history: List[Dict[str, Any]], sector: str) -> float:
    cagr = history[-1]["eps_cagr_5yr"]
    return 70.0 + (cagr - 15.0) * 1.25


register_rule(
    "PRO-09",
    "PRO",
    "Consistent earnings-per-share growth demonstrates value creation for equity holders.",
)((pro_09_cond, pro_09_conf))


# PRO-10: Improving ROE (last 3 years)
def pro_10_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return len(history) >= 3 and (
        history[-1].get("return_on_equity_pct") is not None
        and history[-2].get("return_on_equity_pct") is not None
        and history[-3].get("return_on_equity_pct") is not None
        and history[-1]["return_on_equity_pct"]
        > history[-2]["return_on_equity_pct"]
        > history[-3]["return_on_equity_pct"]
    )


def pro_10_conf(history: List[Dict[str, Any]], sector: str) -> float:
    diff = history[-1]["return_on_equity_pct"] - history[-3]["return_on_equity_pct"]
    return 65.0 + diff * 2.0


register_rule(
    "PRO-10",
    "PRO",
    "A steadily improving return on equity indicates growing profitability on shareholder capital.",
)((pro_10_cond, pro_10_conf))


# PRO-11: Operating Leverage (sales growth > 0 and profit growth > sales growth)
def pro_11_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    if len(history) < 2:
        return False
    latest_sales = history[-1].get("sales", 0.0)
    prev_sales = history[-2].get("sales", 0.0)
    latest_prof = history[-1].get("net_profit", 0.0)
    prev_prof = history[-2].get("net_profit", 0.0)

    if prev_sales <= 0 or prev_prof <= 0:
        return False

    s_growth = (latest_sales - prev_sales) / prev_sales
    p_growth = (latest_prof - prev_prof) / prev_prof
    return s_growth > 0 and p_growth > s_growth


def pro_11_conf(history: List[Dict[str, Any]], sector: str) -> float:
    latest_sales = history[-1].get("sales", 1.0)
    prev_sales = history[-2].get("sales", 1.0)
    latest_prof = history[-1].get("net_profit", 1.0)
    prev_prof = history[-2].get("net_profit", 1.0)
    s_growth = (latest_sales - prev_sales) / prev_sales
    p_growth = (latest_prof - prev_prof) / prev_prof
    return 70.0 + (p_growth - s_growth) * 50.0


register_rule(
    "PRO-11",
    "PRO",
    "Positive operating leverage leads to disproportionate profit growth as sales expand.",
)((pro_11_cond, pro_11_conf))


# PRO-12: Growing Assets + Declining Debt
def pro_12_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return len(history) >= 3 and (
        history[-1].get("total_assets", 0)
        > history[-2].get("total_assets", 0)
        > history[-3].get("total_assets", 0)
        and history[-1].get("borrowings", 999)
        < history[-2].get("borrowings", 999)
        < history[-3].get("borrowings", 999)
    )


def pro_12_conf(history: List[Dict[str, Any]], sector: str) -> float:
    return 80.0


register_rule(
    "PRO-12",
    "PRO",
    "Growing asset base combined with debt reduction strengthens the balance sheet.",
)((pro_12_cond, pro_12_conf))


# =====================================================================
# CON RULES (CON-01 to CON-12)
# =====================================================================


# CON-01: Elevated Debt-to-Equity (>2, non-financials)
def con_01_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 1
        and sector != "Financials"
        and history[-1].get("debt_to_equity") is not None
        and history[-1]["debt_to_equity"] > 2.0
    )


def con_01_conf(history: List[Dict[str, Any]], sector: str) -> float:
    de = history[-1]["debt_to_equity"]
    return 65.0 + (de - 2.0) * 10.0


register_rule(
    "CON-01",
    "CON",
    "Debt-to-equity ratio is elevated for a non-financial company and warrants monitoring.",
)((con_01_cond, con_01_conf))


# CON-02: Negative FCF (last 3 years)
def con_02_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return len(history) >= 3 and all(
        r.get("free_cash_flow_cr") is not None and r["free_cash_flow_cr"] < 0.0
        for r in history[-3:]
    )


def con_02_conf(history: List[Dict[str, Any]], sector: str) -> float:
    return 80.0


register_rule(
    "CON-02",
    "CON",
    "Negative free cash flow for 3 consecutive years indicates cash burn and liquidity risks.",
)((con_02_cond, con_02_conf))


# CON-03: Declining Operating Margin (last 3 years)
def con_03_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return len(history) >= 3 and (
        history[-1].get("operating_profit_margin_pct") is not None
        and history[-2].get("operating_profit_margin_pct") is not None
        and history[-3].get("operating_profit_margin_pct") is not None
        and history[-1]["operating_profit_margin_pct"]
        < history[-2]["operating_profit_margin_pct"]
        < history[-3]["operating_profit_margin_pct"]
    )


def con_03_conf(history: List[Dict[str, Any]], sector: str) -> float:
    diff = (
        history[-3]["operating_profit_margin_pct"]
        - history[-1]["operating_profit_margin_pct"]
    )
    return 65.0 + diff * 2.0


register_rule(
    "CON-03",
    "CON",
    "Consistently declining operating margins signal pressure on profitability or rising costs.",
)((con_03_cond, con_03_conf))


# CON-04: Net Loss in latest year
def con_04_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 1
        and history[-1].get("net_profit") is not None
        and history[-1]["net_profit"] < 0.0
    )


def con_04_conf(history: List[Dict[str, Any]], sector: str) -> float:
    # If net profit margin exists and is negative
    npm = history[-1].get("net_profit_margin_pct", -5.0)
    return 80.0 + abs(npm) * 0.5


register_rule("CON-04", "CON", "Company reported a net loss in the latest period.")(
    (con_04_cond, con_04_conf)
)


# CON-05: Revenue Decline (latest year vs 1 year ago)
def con_05_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 2
        and history[-1].get("sales") is not None
        and history[-2].get("sales") is not None
        and history[-1]["sales"] < history[-2]["sales"]
    )


def con_05_conf(history: List[Dict[str, Any]], sector: str) -> float:
    dec = (history[-2]["sales"] - history[-1]["sales"]) / history[-2]["sales"]
    return 70.0 + dec * 150.0


register_rule(
    "CON-05",
    "CON",
    "Declining revenues signal shrinking business activity or market share loss.",
)((con_05_cond, con_05_conf))


# CON-06: Low Interest Coverage (ICR < 1.5, non-financials)
def con_06_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 1
        and sector != "Financials"
        and history[-1].get("interest_coverage") is not None
        and history[-1]["interest_coverage"] < 1.5
    )


def con_06_conf(history: List[Dict[str, Any]], sector: str) -> float:
    icr = history[-1]["interest_coverage"]
    return 75.0 + (1.5 - icr) * 15.0


register_rule(
    "CON-06",
    "CON",
    "Low interest coverage ratio signals potential difficulty in servicing debt obligations.",
)((con_06_cond, con_06_conf))


# CON-07: Unstable Dividend Payout (>100% and <1000%)
def con_07_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 1
        and history[-1].get("dividend_payout_ratio_pct") is not None
        and 100.0 < history[-1]["dividend_payout_ratio_pct"] < 1000.0
    )


def con_07_conf(history: List[Dict[str, Any]], sector: str) -> float:
    payout = history[-1]["dividend_payout_ratio_pct"]
    return 70.0 + (payout - 100.0) * 0.1


register_rule(
    "CON-07",
    "CON",
    "Dividend payout exceeding 100% of earnings is unsustainable in the long term.",
)((con_07_cond, con_07_conf))


# CON-08: Rising Debt (last 3 years)
def con_08_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return len(history) >= 3 and (
        history[-1].get("total_debt_cr", 0)
        > history[-2].get("total_debt_cr", 0)
        > history[-3].get("total_debt_cr", 0)
    )


def con_08_conf(history: List[Dict[str, Any]], sector: str) -> float:
    diff = (history[-1]["total_debt_cr"] - history[-3]["total_debt_cr"]) / max(
        history[-3]["total_debt_cr"], 1.0
    )
    return 65.0 + diff * 100.0


register_rule(
    "CON-08", "CON", "Steadily rising borrowings increases leverage and financial risk."
)((con_08_cond, con_08_conf))


# CON-09: Falling EPS (last 3 years)
def con_09_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return len(history) >= 3 and (
        history[-1].get("earnings_per_share") is not None
        and history[-2].get("earnings_per_share") is not None
        and history[-3].get("earnings_per_share") is not None
        and history[-1]["earnings_per_share"]
        < history[-2]["earnings_per_share"]
        < history[-3]["earnings_per_share"]
    )


def con_09_conf(history: List[Dict[str, Any]], sector: str) -> float:
    return 75.0


register_rule(
    "CON-09",
    "CON",
    "Declining earnings per share indicates shrinking profitability for equity holders.",
)((con_09_cond, con_09_conf))


# CON-10: Low ROCE (<10% in latest year)
def con_10_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 1
        and history[-1].get("return_on_capital_employed_pct") is not None
        and history[-1]["return_on_capital_employed_pct"] < 10.0
    )


def con_10_conf(history: List[Dict[str, Any]], sector: str) -> float:
    roce = history[-1]["return_on_capital_employed_pct"]
    return 65.0 + (10.0 - roce) * 2.0


register_rule(
    "CON-10",
    "CON",
    "Low return on capital employed indicates suboptimal efficiency in deploying capital.",
)((con_10_cond, con_10_conf))


# CON-11: High Net Debt (Debt-to-Assets > 50%, non-financials)
def con_11_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    if sector == "Financials" or len(history) < 1:
        return False
    debt = history[-1].get("borrowings", 0.0)
    assets = history[-1].get("total_assets", 0.0)
    return assets > 0 and (debt / assets) > 0.5


def con_11_conf(history: List[Dict[str, Any]], sector: str) -> float:
    ratio = history[-1]["borrowings"] / history[-1]["total_assets"]
    return 70.0 + (ratio - 0.5) * 50.0


register_rule(
    "CON-11",
    "CON",
    "Elevated debt relative to asset base limits financial flexibility.",
)((con_11_cond, con_11_conf))


# CON-12: Weak Revenue CAGR (<5%)
def con_12_cond(history: List[Dict[str, Any]], sector: str) -> bool:
    return (
        len(history) >= 1
        and history[-1].get("revenue_cagr_5yr") is not None
        and history[-1]["revenue_cagr_5yr"] < 5.0
    )


def con_12_conf(history: List[Dict[str, Any]], sector: str) -> float:
    cagr = history[-1]["revenue_cagr_5yr"]
    return 65.0 + (5.0 - cagr) * 5.0


register_rule(
    "CON-12",
    "CON",
    "Stagnant or low revenue growth indicates a lack of expansion momentum.",
)((con_12_cond, con_12_conf))
