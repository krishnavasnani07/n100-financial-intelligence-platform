"""
Cluster Profiling, Correlation Analysis, Outlier Detection, and Portfolio Statistics Module.
Processes cluster output and generates downstream portfolio intelligence reports.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.config.settings import BASE_DIR, DB_PATH, OUTPUT_DIR
from src.screener.ranking import calculate_rankings


def get_profile_logger() -> logging.Logger:
    """
    Configures a logger that logs to logs/clustering.log and stdout.
    """
    logger = logging.getLogger("cluster_profile")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        # Ensure logs directory exists
        log_dir = BASE_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "clustering.log"

        # File Handler
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Stream Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


logger = get_profile_logger()


def load_cluster_data(db_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads latest company ratio data and merges it with yesterday's cluster assignments.
    """
    db_file = db_path or DB_PATH
    logger.info(f"Loading company ratio data from db: {db_file}")
    df_ratios = calculate_rankings(db_file)
    
    labels_file = OUTPUT_DIR / "cluster_labels.csv"
    logger.info(f"Loading cluster labels from: {labels_file}")
    if not labels_file.exists():
        raise FileNotFoundError(f"Missing required cluster labels: {labels_file}")
        
    df_labels = pd.read_csv(labels_file)
    
    # Merge assignments
    df_merged = pd.merge(
        df_ratios,
        df_labels[["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]],
        on="company_id",
        how="inner"
    )
    
    # Assertions
    assert len(df_merged) == 92, f"Expected 92 companies after merge, got {len(df_merged)}"
    logger.info("Successfully merged cluster assignments and ratio data.")
    return df_merged


def impute_clustering_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Imputes the 5 clustering features to maintain profile alignment with KMeans input.
    """
    features = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct"
    ]
    df_imputed = df.copy()
    for feat in features:
        sector_medians = df_imputed.groupby("sector")[feat].transform("median")
        df_imputed[feat] = df_imputed[feat].fillna(sector_medians)
        global_median = df_imputed[feat].median()
        df_imputed[feat] = df_imputed[feat].fillna(global_median)
    return df_imputed


def profile_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates mean and median for the 5 clustering features across each cluster.
    """
    logger.info("Calculating cluster statistics (mean and median)...")
    
    features = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct"
    ]
    
    profiles = []
    
    for cid, group in df.groupby("cluster_id"):
        cluster_name = group["cluster_name"].iloc[0]
        company_count = len(group)
        
        row = {
            "cluster_id": int(cid),
            "cluster_name": cluster_name,
            "company_count": int(company_count),
            
            "roe_mean": round(float(group["return_on_equity_pct"].mean()), 4),
            "roe_median": round(float(group["return_on_equity_pct"].median()), 4),
            
            "de_mean": round(float(group["debt_to_equity"].mean()), 4),
            "de_median": round(float(group["debt_to_equity"].median()), 4),
            
            "revenue_cagr_mean": round(float(group["revenue_cagr_5yr"].mean()), 4),
            "revenue_cagr_median": round(float(group["revenue_cagr_5yr"].median()), 4),
            
            "fcf_cagr_mean": round(float(group["fcf_cagr_5yr"].mean()), 4),
            "fcf_cagr_median": round(float(group["fcf_cagr_5yr"].median()), 4),
            
            "opm_mean": round(float(group["operating_profit_margin_pct"].mean()), 4),
            "opm_median": round(float(group["operating_profit_margin_pct"].median()), 4),
        }
        profiles.append(row)
        
    profiles_df = pd.DataFrame(profiles).sort_values("cluster_id")
    
    profiles_file = OUTPUT_DIR / "cluster_profiles.csv"
    profiles_df.to_csv(profiles_file, index=False)
    logger.info(f"Cluster profiles successfully saved to: {profiles_file}")
    
    return profiles_df


def print_cluster_companies(df: pd.DataFrame) -> None:
    """
    Prints constituent companies and their metric distances for each cluster.
    """
    logger.info("\n=========================================")
    logger.info("Cluster Constituent Analysis")
    logger.info("=========================================")
    
    features = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct"
    ]
    
    for cid, group in df.groupby("cluster_id"):
        cluster_name = group["cluster_name"].iloc[0]
        logger.info(f"\nCluster {cid} — {cluster_name} ({len(group)} companies):")
        logger.info("-" * 110)
        logger.info(f"{'Company ID':<12} | {'ROE (%)':<8} | {'D/E':<6} | {'Rev CAGR (%)':<12} | {'FCF CAGR (%)':<12} | {'OPM (%)':<8} | {'Distance':<8}")
        logger.info("-" * 110)
        for _, row in group.sort_values("distance_from_centroid").iterrows():
            logger.info(
                f"{row['company_id']:<12} | "
                f"{row['return_on_equity_pct']:>8.2f} | "
                f"{row['debt_to_equity']:>6.2f} | "
                f"{row['revenue_cagr_5yr']:>12.2f} | "
                f"{row['fcf_cagr_5yr']:>12.2f} | "
                f"{row['operating_profit_margin_pct']:>8.2f} | "
                f"{row['distance_from_centroid']:>8.4f}"
            )


def generate_correlation_heatmap(df: pd.DataFrame) -> None:
    """
    Computes Pearson correlation for 10 KPIs and saves heatmap to reports/correlation_heatmap.png.
    """
    logger.info("Computing Pearson correlation matrix for 10 KPIs...")
    kpis = [
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "pat_cagr_5yr",
        "revenue_cagr_5yr",
        "eps_cagr_5yr",
        "interest_coverage",
        "asset_turnover"
    ]
    
    corr = df[kpis].corr(method="pearson")
    
    # Validation checks
    assert corr.shape == (10, 10), f"Expected 10x10 shape, got {corr.shape}"
    for i in range(10):
        assert abs(corr.iloc[i, i] - 1.0) < 1e-7, f"Diagonal element at {i} is not 1"
        for j in range(10):
            assert abs(corr.iloc[i, j] - corr.iloc[j, i]) < 1e-7, f"Asymmetric correlation at ({i}, {j})"
            
    logger.info("Correlation matrix validations passed (10x10, symmetric, diagonal=1).")
    
    # Save plot
    labels = [k.replace("_pct", "").replace("_5yr", "").replace("_cr", "").replace("_", " ").title() for k in kpis]
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        square=True,
        xticklabels=labels,
        yticklabels=labels,
        cbar_kws={"shrink": .8}
    )
    plt.title("Financial KPI Correlation Matrix — Latest Year", fontsize=14, pad=15)
    plt.tight_layout()
    
    plot_path = BASE_DIR / "reports" / "correlation_heatmap.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    logger.info(f"Correlation heatmap saved to: {plot_path}")


def detect_sector_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes sector-based Z-scores for 10 KPIs and flags outliers where |Z| > 3.
    Handles zero standard deviation safely by setting Z-score to 0.
    """
    logger.info("Detecting sector-based outliers using Z-score method (|Z| > 3)...")
    kpis = [
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "pat_cagr_5yr",
        "revenue_cagr_5yr",
        "eps_cagr_5yr",
        "interest_coverage",
        "asset_turnover"
    ]
    
    outliers = []
    
    for sector_name, group in df.groupby("sector"):
        for kpi in kpis:
            non_null = group[kpi].dropna()
            if len(non_null) == 0:
                continue
            
            mean_val = non_null.mean()
            std_val = non_null.std(ddof=0)
            
            for _, row in group.iterrows():
                val = row[kpi]
                if pd.isnull(val):
                    continue
                
                # Zero standard deviation safety
                if pd.isnull(std_val) or std_val == 0:
                    z = 0.0
                else:
                    z = (val - mean_val) / std_val
                
                if abs(z) > 3:
                    outliers.append({
                        "company_id": row["company_id"],
                        "company_name": row.get("company_name", row["company_id"]),
                        "broad_sector": sector_name,
                        "metric": kpi,
                        "value": round(float(val), 4),
                        "sector_mean": round(float(mean_val), 4),
                        "sector_std": round(float(std_val), 4) if not pd.isnull(std_val) else 0.0,
                        "z_score": round(float(z), 4),
                        "outlier_flag": True
                    })
                    
    outliers_df = pd.DataFrame(outliers)
    if outliers_df.empty:
        outliers_df = pd.DataFrame(columns=[
            "company_id", "company_name", "broad_sector", "metric", 
            "value", "sector_mean", "sector_std", "z_score", "outlier_flag"
        ])
        
    outlier_file = OUTPUT_DIR / "outlier_report.csv"
    outliers_df.to_csv(outlier_file, index=False)
    logger.info(f"Sector-based outlier report saved to: {outlier_file}. Flagged {len(outliers_df)} outliers.")
    return outliers_df


def generate_portfolio_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes P10, P25, P50, P75, P90, mean, and std for 10 KPIs and validates bounds.
    """
    logger.info("Generating portfolio percentile statistics...")
    kpis = [
        "return_on_equity_pct",
        "return_on_capital_employed_pct",
        "net_profit_margin_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "pat_cagr_5yr",
        "revenue_cagr_5yr",
        "eps_cagr_5yr",
        "interest_coverage",
        "asset_turnover"
    ]
    
    stats = []
    for kpi in kpis:
        series = df[kpi].dropna()
        p10 = series.quantile(0.10)
        p25 = series.quantile(0.25)
        p50 = series.quantile(0.50)
        p75 = series.quantile(0.75)
        p90 = series.quantile(0.90)
        mean_val = series.mean()
        std_val = series.std()
        
        # Validation checks
        assert p10 <= p25 <= p50 <= p75 <= p90, f"Quantile order violation for '{kpi}': {p10} <= {p25} <= {p50} <= {p75} <= {p90}"
        assert not pd.isnull(mean_val), f"Mean is null for '{kpi}'"
        assert not pd.isnull(std_val), f"Std deviation is null for '{kpi}'"
        
        stats.append({
            "metric": kpi,
            "p10": round(float(p10), 4),
            "p25": round(float(p25), 4),
            "p50": round(float(p50), 4),
            "p75": round(float(p75), 4),
            "p90": round(float(p90), 4),
            "mean": round(float(mean_val), 4),
            "std": round(float(std_val), 4)
        })
        
    stats_df = pd.DataFrame(stats)
    stats_file = OUTPUT_DIR / "portfolio_stats.csv"
    stats_df.to_csv(stats_file, index=False)
    logger.info(f"Portfolio statistics saved to: {stats_file}")
    return stats_df


def main() -> None:
    logger.info("=========================================")
    logger.info("Starting S6 Day 37 Profiling & Stats Engine")
    logger.info("=========================================")
    
    try:
        # Load S6 Day 36 cluster data
        df = load_cluster_data()
        
        # Impute clustering features to match centroids in standardize space
        df_imputed = impute_clustering_features(df)
        
        # Profile clusters
        profile_clusters(df_imputed)
        
        # Constituent display
        print_cluster_companies(df_imputed)
        
        # Heatmap
        generate_correlation_heatmap(df)
        
        # Sector Outliers
        detect_sector_outliers(df)
        
        # Portfolio Stats
        generate_portfolio_stats(df)
        
        logger.info("=========================================")
        logger.info("S6 Day 37 Execution Completed Successfully")
        logger.info("=========================================")
        
    except Exception as e:
        logger.error(f"Execution failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
