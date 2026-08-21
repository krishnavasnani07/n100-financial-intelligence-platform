from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Optional

from src.repositories.peer_repository import PeerRepository, SQLitePeerRepository
from src.repositories.ratio_repository import RatioRepository, SQLiteRatioRepository


class ExplanationEngine:
    def __init__(
        self,
        ratio_repo: Optional[RatioRepository] = None,
        peer_repo: Optional[PeerRepository] = None,
        db_path: Optional[Path | str] = None,
    ):
        self.ratio_repo = ratio_repo or SQLiteRatioRepository(db_path)
        self.peer_repo = peer_repo or SQLitePeerRepository(db_path)

    def explain_roe_change(
        self, company_id: str, year_1: str, year_2: str
    ) -> dict[str, Any]:
        """
        Executes a 3-step DuPont Analysis attribution for the change in Return on Equity (ROE)
        between two years.

        Attribution formula (exact additive breakdown):
          - NPM Contribution = (NPM_2 - NPM_1) * ATO_1 * FL_1 * 100
          - ATO Contribution = NPM_2 * (ATO_2 - ATO_1) * FL_1 * 100
          - FL Contribution = NPM_2 * ATO_2 * (FL_2 - FL_1) * 100
        """
        # Fetch statements
        pnl_statements = self.ratio_repo.get_pnl_by_company(company_id)
        bs_statements = self.ratio_repo.get_balancesheet_by_company(company_id)

        # Index by year
        pnl_map = {stmt.year: stmt for stmt in pnl_statements}
        bs_map = {stmt.year: stmt for stmt in bs_statements}

        if year_1 not in pnl_map or year_1 not in bs_map:
            raise ValueError(f"Data not found for company {company_id} in {year_1}")
        if year_2 not in pnl_map or year_2 not in bs_map:
            raise ValueError(f"Data not found for company {company_id} in {year_2}")

        p1, p2 = pnl_map[year_1], pnl_map[year_2]
        b1, b2 = bs_map[year_1], bs_map[year_2]

        # Year 1 Metrics
        sales_1 = p1.sales or 0.0
        net_profit_1 = p1.net_profit or 0.0
        total_assets_1 = b1.total_assets or 0.0
        equity_1 = (b1.equity_capital or 0.0) + (b1.reserves or 0.0)

        # Year 2 Metrics
        sales_2 = p2.sales or 0.0
        net_profit_2 = p2.net_profit or 0.0
        total_assets_2 = b2.total_assets or 0.0
        equity_2 = (b2.equity_capital or 0.0) + (b2.reserves or 0.0)

        # DuPont Components
        npm_1 = (net_profit_1 / sales_1) if sales_1 > 0 else 0.0
        npm_2 = (net_profit_2 / sales_2) if sales_2 > 0 else 0.0

        ato_1 = (sales_1 / total_assets_1) if total_assets_1 > 0 else 0.0
        ato_2 = (sales_2 / total_assets_2) if total_assets_2 > 0 else 0.0

        fl_1 = (total_assets_1 / equity_1) if equity_1 > 0 else 0.0
        fl_2 = (total_assets_2 / equity_2) if equity_2 > 0 else 0.0

        roe_1 = npm_1 * ato_1 * fl_1 * 100
        roe_2 = npm_2 * ato_2 * fl_2 * 100
        roe_change = roe_2 - roe_1

        # Additive Contributions
        npm_contrib = (npm_2 - npm_1) * ato_1 * fl_1 * 100
        ato_contrib = npm_2 * (ato_2 - ato_1) * fl_1 * 100
        fl_contrib = npm_2 * ato_2 * (fl_2 - fl_1) * 100

        # Primary Driver Analysis
        contribs = {
            "Operating Efficiency (NPM)": npm_contrib,
            "Asset Use Efficiency (ATO)": ato_contrib,
            "Financial Leverage (FL)": fl_contrib,
        }
        primary_driver = max(contribs.keys(), key=lambda k: abs(contribs[k]))
        primary_contrib = contribs[primary_driver]

        direction = "positive" if primary_contrib > 0 else "negative"

        explanation_str = (
            f"ROE changed from {roe_1:.2f}% to {roe_2:.2f}% (difference of {roe_change:+.2f} percentage points). "
            f"The primary {direction} driver was {primary_driver}, which contributed {primary_contrib:+.2f} percentage points to the change. "
        )

        if primary_driver == "Operating Efficiency (NPM)":
            explanation_str += f"Net profit margins changed from {npm_1 * 100:.1f}% to {npm_2 * 100:.1f}%, indicating a shift in operational profitability."
        elif primary_driver == "Asset Use Efficiency (ATO)":
            explanation_str += f"Asset turnover moved from {ato_1:.2f}x to {ato_2:.2f}x, reflecting changes in how efficiently assets generated sales."
        elif primary_driver == "Financial Leverage (FL)":
            explanation_str += f"Financial leverage moved from {fl_1:.2f} to {fl_2:.2f}, indicating changes in the capital structure and debt dependency."

        return {
            "company_id": company_id,
            "year_1": year_1,
            "year_2": year_2,
            "roe_1": round(roe_1, 2),
            "roe_2": round(roe_2, 2),
            "roe_change": round(roe_change, 2),
            "npm_1": round(npm_1 * 100, 2),
            "npm_2": round(npm_2 * 100, 2),
            "ato_1": round(ato_1, 2),
            "ato_2": round(ato_2, 2),
            "fl_1": round(fl_1, 2),
            "fl_2": round(fl_2, 2),
            "contributions": {
                "operating_efficiency_npm": round(npm_contrib, 2),
                "asset_efficiency_ato": round(ato_contrib, 2),
                "financial_leverage_fl": round(fl_contrib, 2),
            },
            "primary_driver": primary_driver,
            "primary_contribution": round(primary_contrib, 2),
            "explanation": explanation_str,
        }

    def _get_metric_subscore(self, kpi: str, val: Optional[float], de_ratio: Optional[float] = None) -> float:
        """Helper to calculate individual normalized score components."""
        if val is None or math.isnan(val):
            return 0.0

        if kpi in ["roe", "roce"]:
            return min(100.0, max(0.0, (val / 20.0) * 100.0))
        elif kpi in ["revenue_cagr", "pat_cagr"]:
            return min(100.0, max(0.0, (val / 15.0) * 100.0))
        elif kpi == "debt_to_equity":
            if val <= 0.5:
                return 100.0
            elif val >= 2.0:
                return 0.0
            else:
                return (2.0 - val) / 1.5 * 100.0
        elif kpi == "interest_coverage":
            if val >= 10.0:
                return 100.0
            elif val <= 1.0:
                return 0.0
            else:
                return (val - 1.0) / 9.0 * 100.0
        elif kpi == "cfo_quality":
            return min(100.0, max(0.0, val * 100.0))
        return 0.0

    def explain_quality_score_change(
        self, company_id: str, year_1: str, year_2: str
    ) -> dict[str, Any]:
        """
        Attributes changes in the Composite Quality Score between two years to its underlying 7 KPIs.
        """
        r1 = self.ratio_repo.get_by_company_and_year(company_id, year_1)
        r2 = self.ratio_repo.get_by_company_and_year(company_id, year_2)

        if not r1:
            raise ValueError(f"Ratios not found for company {company_id} in {year_1}")
        if not r2:
            raise ValueError(f"Ratios not found for company {company_id} in {year_2}")

        score_1 = r1.composite_quality_score or 0.0
        score_2 = r2.composite_quality_score or 0.0
        score_change = score_2 - score_1

        # We need to compute CFO Quality for both years
        # CFO Quality = CFO / Net Profit
        pnl_1 = self.ratio_repo.get_pnl_by_company(company_id)
        pnl_map = {stmt.year: stmt for stmt in pnl_1}
        
        p1 = pnl_map.get(year_1)
        p2 = pnl_map.get(year_2)
        
        np_1 = p1.net_profit if p1 else None
        np_2 = p2.net_profit if p2 else None
        
        cfo_1 = r1.cash_from_operations_cr
        cfo_2 = r2.cash_from_operations_cr
        
        cfo_q_1 = (cfo_1 / np_1) if cfo_1 is not None and np_1 is not None and np_1 > 0 else 0.0
        cfo_q_2 = (cfo_2 / np_2) if cfo_2 is not None and np_2 is not None and np_2 > 0 else 0.0

        # Components configuration: (name, key, weight)
        kpi_configs = [
            ("ROE", "roe", 0.20, r1.return_on_equity_pct, r2.return_on_equity_pct),
            ("ROCE", "roce", 0.20, r1.return_on_capital_employed_pct, r2.return_on_capital_employed_pct),
            ("Revenue CAGR", "revenue_cagr", 0.15, r1.revenue_cagr_5yr, r2.revenue_cagr_5yr),
            ("PAT CAGR", "pat_cagr", 0.15, r1.pat_cagr_5yr, r2.pat_cagr_5yr),
            ("Debt to Equity", "debt_to_equity", 0.10, r1.debt_to_equity, r2.debt_to_equity),
            ("Interest Coverage", "interest_coverage", 0.10, r1.interest_coverage, r2.interest_coverage),
            ("CFO Quality", "cfo_quality", 0.10, cfo_q_1, cfo_q_2),
        ]

        # Calculate contributions
        drivers = {}
        weighted_sum_1 = 0.0
        weight_sum_1 = 0.0
        weighted_sum_2 = 0.0
        weight_sum_2 = 0.0

        components_data = []

        for name, key, weight, v1, v2 in kpi_configs:
            # Re-check nulls dynamically matching the algorithm in populate_financial_ratios.py
            is_valid_1 = v1 is not None and not math.isnan(v1)
            is_valid_2 = v2 is not None and not math.isnan(v2)

            sub_1 = self._get_metric_subscore(key, v1, de_ratio=r1.debt_to_equity) if is_valid_1 else 0.0
            sub_2 = self._get_metric_subscore(key, v2, de_ratio=r2.debt_to_equity) if is_valid_2 else 0.0

            if is_valid_1:
                weighted_sum_1 += sub_1 * weight
                weight_sum_1 += weight
            if is_valid_2:
                weighted_sum_2 += sub_2 * weight
                weight_sum_2 += weight

            components_data.append({
                "kpi": name,
                "val_1": v1,
                "val_2": v2,
                "subscore_1": sub_1,
                "subscore_2": sub_2,
                "weight": weight
            })

        # Calculate exact change contributions
        # Since the overall score is weighted_sum / weight_sum, changes are:
        # Score = Sum(sub_i * weight_i) / Weight_Sum
        # Contribution_i = (sub_i_2 * weight_i / Weight_Sum_2) - (sub_i_1 * weight_i / Weight_Sum_1)
        w_sum_1 = weight_sum_1 if weight_sum_1 > 0 else 1.0
        w_sum_2 = weight_sum_2 if weight_sum_2 > 0 else 1.0

        for comp in components_data:
            contrib_1 = (comp["subscore_1"] * comp["weight"]) / w_sum_1
            contrib_2 = (comp["subscore_2"] * comp["weight"]) / w_sum_2
            change = contrib_2 - contrib_1
            drivers[comp["kpi"]] = round(change, 2)

        # Primary drivers
        positive_drivers = {k: v for k, v in drivers.items() if v > 0.01}
        negative_drivers = {k: v for k, v in drivers.items() if v < -0.01}

        explanation_str = f"Composite Quality Score changed from {score_1:.1f} to {score_2:.1f} ({score_change:+.1f} points). "
        
        if positive_drivers:
            pos_desc = ", ".join([f"{k} ({v:+.1f})" for k, v in sorted(positive_drivers.items(), key=lambda x: x[1], reverse=True)])
            explanation_str += f"Primary positive drivers: {pos_desc}. "
        if negative_drivers:
            neg_desc = ", ".join([f"{k} ({v:.1f})" for k, v in sorted(negative_drivers.items(), key=lambda x: x[1])])
            explanation_str += f"Primary negative drivers: {neg_desc}. "
        if not positive_drivers and not negative_drivers:
            explanation_str += "The underlying scoring parameters remained stable."

        return {
            "company_id": company_id,
            "year_1": year_1,
            "year_2": year_2,
            "score_1": score_1,
            "score_2": score_2,
            "score_change": round(score_change, 2),
            "drivers": drivers,
            "explanation": explanation_str,
        }

    def generate_peer_relative_explanation(
        self, company_id: str, year: str
    ) -> dict[str, Any]:
        """
        Compares the company's key ratios against its sector medians for the specified year
        and returns explanations.
        """
        # Fetch company's sector
        sector_info = self.peer_repo.get_sector_by_company(company_id)
        if not sector_info or not sector_info.broad_sector:
            return {"explanation": "No sector classification found for this company."}

        sector = sector_info.broad_sector

        # Get company's latest ratios
        ratios = self.ratio_repo.get_by_company_and_year(company_id, year)
        if not ratios:
            return {"explanation": f"Ratios not found for {company_id} in {year}."}

        # Fetch sector benchmark statistics
        kpis = ["ROE", "Operating Margin", "Debt to Equity", "Composite Quality Score"]
        sector_stats = self.peer_repo.get_sector_statistics(sector, kpis)
        stats_map = {stat.kpi: stat for stat in sector_stats}

        explanations = []

        # ROE Comparison
        roe = ratios.return_on_equity_pct
        if roe is not None and "ROE" in stats_map:
            median_roe = stats_map["ROE"].median
            diff = roe - median_roe
            if diff > 5.0:
                explanations.append(f"ROE of {roe:.1f}% exceeds the {sector} peer median ({median_roe:.1f}%) by {diff:.1f} percentage points, showing premium profitability.")
            elif diff < -5.0:
                explanations.append(f"ROE of {roe:.1f}% lags behind the {sector} peer median ({median_roe:.1f}%) by {abs(diff):.1f} percentage points.")

        # Margin Comparison
        margin = ratios.operating_profit_margin_pct
        if margin is not None and "Operating Margin" in stats_map:
            median_margin = stats_map["Operating Margin"].median
            diff = margin - median_margin
            if diff > 5.0:
                explanations.append(f"Operating margin of {margin:.1f}% is significantly higher than the peer median ({median_margin:.1f}%), indicating strong pricing power.")
            elif diff < -5.0:
                explanations.append(f"Operating margin of {margin:.1f}% is below the peer median ({median_margin:.1f}%), indicating higher cost structures.")

        # Debt to Equity
        de = ratios.debt_to_equity
        if de is not None and "Debt to Equity" in stats_map:
            median_de = stats_map["Debt to Equity"].median
            if de <= 0.1:
                explanations.append("The company maintains a virtually debt-free balance sheet, representing low leverage risk.")
            elif de > 1.5 * median_de:
                explanations.append(f"Debt/Equity of {de:.2f} is higher than the peer median ({median_de:.2f}), indicating elevated leverage.")

        explanation_str = " ".join(explanations)
        if not explanation_str:
            explanation_str = f"The company's financial indicators are closely aligned with the {sector} sector medians."

        return {
            "company_id": company_id,
            "year": year,
            "sector": sector,
            "metrics": {
                "company_roe": roe,
                "sector_median_roe": stats_map["ROE"].median if "ROE" in stats_map else None,
                "company_opm": margin,
                "sector_median_opm": stats_map["Operating Margin"].median if "Operating Margin" in stats_map else None,
                "company_de": de,
                "sector_median_de": stats_map["Debt to Equity"].median if "Debt to Equity" in stats_map else None,
            },
            "explanation": explanation_str,
        }
