from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

from src.repositories.company_repository import CompanyRepository, SQLiteCompanyRepository
from src.repositories.ratio_repository import RatioRepository, SQLiteRatioRepository


class FinancialDNAEngine:
    def __init__(
        self,
        company_repo: Optional[CompanyRepository] = None,
        ratio_repo: Optional[RatioRepository] = None,
        db_path: Optional[Path | str] = None,
    ):
        self.company_repo = company_repo or SQLiteCompanyRepository(db_path)
        self.ratio_repo = ratio_repo or SQLiteRatioRepository(db_path)
        self.db_path = db_path

    def prepare_features(self, year: str) -> pd.DataFrame:
        """
        Loads key financial metrics for all companies for a given year and returns
        a DataFrame of features ready for clustering.
        """
        companies = self.company_repo.get_all()
        records = []

        for comp in companies:
            ratio = self.ratio_repo.get_by_company_and_year(comp.id, year)
            if not ratio:
                continue

            records.append({
                "company_id": comp.id,
                "roe": ratio.return_on_equity_pct,
                "roce": ratio.return_on_capital_employed_pct,
                "revenue_cagr": ratio.revenue_cagr_5yr,
                "pat_cagr": ratio.pat_cagr_5yr,
                "debt_to_equity": ratio.debt_to_equity,
                "interest_coverage": ratio.interest_coverage,
                "opm": ratio.operating_profit_margin_pct,
            })

        if not records:
            raise ValueError(f"No ratios found for year {year}")

        df = pd.DataFrame(records).set_index("company_id")

        # Impute missing values with column medians
        for col in df.columns:
            median_val = df[col].median()
            # If everything is null for a column, default to 0.0
            if pd.isnull(median_val):
                median_val = 0.0
            df[col] = df[col].fillna(median_val)

        return df

    def fit_clusters(
        self, df_features: pd.DataFrame, n_clusters: int = 4
    ) -> dict[str, Any]:
        """
        Fits KMeans, GMM, and Agglomerative Clustering models.
        Evaluates clustering quality via a weighted Financial Cluster Quality Score.
        """
        if len(df_features) < n_clusters:
            raise ValueError(f"Dataset has only {len(df_features)} samples, which is fewer than n_clusters ({n_clusters})")

        # Scale features
        scaler = StandardScaler()
        X = scaler.fit_transform(df_features)

        # 1. Fit KMeans (Primary model)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        kmeans_labels = kmeans.fit_predict(X)

        # 2. Fit GMM
        gmm = GaussianMixture(n_components=n_clusters, random_state=42)
        gmm.fit(X)
        gmm_labels = gmm.predict(X)

        # 3. Fit Agglomerative Clustering
        agg = AgglomerativeClustering(n_clusters=n_clusters)
        agg_labels = agg.fit_predict(X)

        # Compute validation metrics for KMeans (primary model)
        sil = float(silhouette_score(X, kmeans_labels))
        db = float(davies_bouldin_score(X, kmeans_labels))
        ch = float(calinski_harabasz_score(X, kmeans_labels))

        # Bootstrap Stability Analysis (Adjusted Rand Index)
        stability_scores = []
        rng = np.random.default_rng(42)
        indices = np.arange(len(df_features))

        for _ in range(10):
            # Bootstrap sample: select 90% of rows
            sample_size = int(len(df_features) * 0.9)
            sample_idx = rng.choice(indices, size=sample_size, replace=False)
            X_sample = X[sample_idx]
            
            # Re-cluster bootstrap sample
            kmeans_sub = KMeans(n_clusters=n_clusters, random_state=42, n_init=5)
            kmeans_sub.fit(X_sample)
            sub_labels = kmeans_sub.labels_
            
            # Original labels for sample rows
            orig_labels_sample = kmeans_labels[sample_idx]
            
            # Compare using Adjusted Rand Index (ARI)
            ari = adjusted_rand_score(orig_labels_sample, sub_labels)
            stability_scores.append(ari)
            
        stability_score = float(np.mean(stability_scores))

        # Financial Interpretability Score (R-squared/variance reduction for ROE and Debt to Equity)
        tot_var_roe = df_features["roe"].var()
        tot_var_de = df_features["debt_to_equity"].var()

        df_kmeans = df_features.copy()
        df_kmeans["cluster"] = kmeans_labels

        # Within-cluster variances
        within_var_roe = 0.0
        within_var_de = 0.0

        for c in range(n_clusters):
            c_data = df_kmeans[df_kmeans["cluster"] == c]
            if len(c_data) > 1:
                within_var_roe += c_data["roe"].var() * (len(c_data) - 1)
                within_var_de += c_data["debt_to_equity"].var() * (len(c_data) - 1)

        # Normalize variance reduction (weighted average of cluster variances vs total variance)
        N = len(df_features)
        r2_roe = 1.0 - (within_var_roe / (tot_var_roe * (N - 1))) if tot_var_roe > 0 else 0.0
        r2_de = 1.0 - (within_var_de / (tot_var_de * (N - 1))) if tot_var_de > 0 else 0.0

        interpretability_score = float(max(0.0, min(1.0, (r2_roe + r2_de) / 2.0)) * 100)

        # Scale statistical indicators to 0-100
        scaled_sil = float(max(0.0, (sil + 1.0) / 2.0 * 100))
        scaled_db = float(max(0.0, 100.0 / (1.0 + db)))
        scaled_ch = float(max(0.0, min(100.0, (ch / 200.0) * 100.0)))
        scaled_stab = float(max(0.0, min(100.0, stability_score * 100)))

        # Weighted calculation of the Financial Cluster Quality Score
        quality_score = (
            scaled_sil * 0.30 +
            scaled_db * 0.20 +
            scaled_ch * 0.15 +
            scaled_stab * 0.20 +
            interpretability_score * 0.15
        )

        # Assign Dynamic Archetypes
        # Compute centroids of kmeans clusters
        centroids = []
        for c in range(n_clusters):
            c_data = df_features[kmeans_labels == c]
            centroids.append({
                "cluster_id": c,
                "roe": float(c_data["roe"].mean()),
                "opm": float(c_data["opm"].mean()),
                "revenue_cagr": float(c_data["revenue_cagr"].mean()),
                "debt_to_equity": float(c_data["debt_to_equity"].mean()),
                "count": len(c_data)
            })

        # Rank clusters dynamically to assign named archetypes
        # Highest average ROE and low leverage -> High-Quality Compounder
        # Highest average Revenue CAGR -> Growth Accelerator
        # Highest Debt to Equity -> Capital Intensive / High Leverage
        # Lowest ROE -> Low-Efficiency Laggard
        # If there are overlaps, we apply a sorting hierarchy
        sorted_by_roe = sorted(centroids, key=lambda x: x["roe"], reverse=True)
        sorted_by_cagr = sorted(centroids, key=lambda x: x["revenue_cagr"], reverse=True)
        sorted_by_de = sorted(centroids, key=lambda x: x["debt_to_equity"], reverse=True)

        archetype_map = {}
        assigned = set()

        # 1. High-Quality Compounder (Highest ROE)
        hq_comp = sorted_by_roe[0]
        archetype_map[hq_comp["cluster_id"]] = "High-Quality Compounder"
        assigned.add(hq_comp["cluster_id"])

        # 2. Capital Intensive / High Leverage (Highest D/E not yet assigned)
        leverage_cluster = next(c for c in sorted_by_de if c["cluster_id"] not in assigned)
        # Verify if leverage is high enough, else label it "Asset Heavy"
        if leverage_cluster["debt_to_equity"] > 0.5:
            archetype_map[leverage_cluster["cluster_id"]] = "High Leverage / Debt Dependent"
        else:
            archetype_map[leverage_cluster["cluster_id"]] = "Asset Heavy / Core Value"
        assigned.add(leverage_cluster["cluster_id"])

        # 3. Growth Accelerator (Highest CAGR not yet assigned)
        growth_cluster = next(c for c in sorted_by_cagr if c["cluster_id"] not in assigned)
        archetype_map[growth_cluster["cluster_id"]] = "Growth Accelerator"
        assigned.add(growth_cluster["cluster_id"])

        # 4. Low-Efficiency Laggard (remaining cluster, usually lowest ROE)
        remaining_cluster = next(c for c in centroids if c["cluster_id"] not in assigned)
        archetype_map[remaining_cluster["cluster_id"]] = "Low-Efficiency Laggard"

        # Apply labels back to centroids list
        for cent in centroids:
            cent["archetype"] = archetype_map[cent["cluster_id"]]

        return {
            "kmeans_labels": kmeans_labels.tolist(),
            "gmm_labels": gmm_labels.tolist(),
            "agg_labels": agg_labels.tolist(),
            "centroids": centroids,
            "metrics": {
                "silhouette_score": round(sil, 4),
                "davies_bouldin_index": round(db, 4),
                "calinski_harabasz_index": round(ch, 4),
                "bootstrap_stability": round(stability_score, 4),
                "financial_interpretability": round(interpretability_score, 4),
            },
            "financial_cluster_quality_score": round(quality_score, 2),
            "archetype_map": archetype_map
        }

    def get_company_dna(self, company_id: str, year: str) -> dict[str, Any]:
        """
        Calculates the financial DNA for a specific company by fitting clusters to the entire
        N100 universe for that year.
        """
        df_features = self.prepare_features(year)
        if company_id not in df_features.index:
            raise ValueError(f"Company {company_id} not found in database for year {year}")

        fit_res = self.fit_clusters(df_features)

        # Get company's cluster and archetype
        idx = list(df_features.index).index(company_id)
        cluster_id = fit_res["kmeans_labels"][idx]
        archetype = fit_res["archetype_map"][cluster_id]

        company_metrics = df_features.loc[company_id].to_dict()
        cluster_centroid = next(c for c in fit_res["centroids"] if c["cluster_id"] == cluster_id)

        return {
            "company_id": company_id,
            "year": year,
            "cluster_id": cluster_id,
            "archetype": archetype,
            "metrics": {
                "roe": round(company_metrics["roe"], 2),
                "roce": round(company_metrics["roce"], 2),
                "revenue_cagr": round(company_metrics["revenue_cagr"], 2),
                "pat_cagr": round(company_metrics["pat_cagr"], 2),
                "debt_to_equity": round(company_metrics["debt_to_equity"], 2),
                "interest_coverage": round(company_metrics["interest_coverage"], 2),
                "opm": round(company_metrics["opm"], 2),
            },
            "cluster_average": {
                "roe": round(cluster_centroid["roe"], 2),
                "revenue_cagr": round(cluster_centroid["revenue_cagr"], 2),
                "debt_to_equity": round(cluster_centroid["debt_to_equity"], 2),
                "opm": round(cluster_centroid["opm"], 2),
            },
            "cluster_quality": {
                "financial_cluster_quality_score": fit_res["financial_cluster_quality_score"],
                "metrics": fit_res["metrics"]
            }
        }
