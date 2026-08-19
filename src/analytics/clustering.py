"""
KMeans Financial Clustering Engine for Nifty 100 Financial Intelligence Platform.
Implements data loading, sector-median imputation, StandardScaler normalization,
elbow analysis, centroid distance calculation, dynamic cluster naming, and validation.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src.config.settings import BASE_DIR, DB_PATH, OUTPUT_DIR
from src.screener.ranking import calculate_rankings


def get_clustering_logger() -> logging.Logger:
    """
    Configures a logger that logs both to logs/clustering.log and stdout.
    """
    logger = logging.getLogger("clustering")
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


logger = get_clustering_logger()


def load_clustering_data(db_path: Path | None = None) -> pd.DataFrame:
    """
    Loads latest company ratio data by joining financial ratios and company information.
    """
    db_file = db_path or DB_PATH
    logger.info(f"Loading company and financial ratio data from: {db_file}")

    # We use calculate_rankings which returns the latest available year for each company
    df = calculate_rankings(db_file)
    logger.info(f"Loaded {len(df)} companies' latest financial records.")
    return df


def impute_sector_medians(df: pd.DataFrame) -> pd.DataFrame:
    """
    Imputes missing values with sector median for each metric, falling back to global median.
    """
    features = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]

    df_imputed = df.copy()

    for feat in features:
        null_count = df_imputed[feat].isna().sum()
        if null_count > 0:
            logger.info(f"Detected {null_count} missing values in feature: '{feat}'")

            # 1. Sector median imputation
            sector_medians = df_imputed.groupby("sector")[feat].transform("median")
            df_imputed[feat] = df_imputed[feat].fillna(sector_medians)

            # Check if any missing values remain (if a sector has all missing values)
            remaining_nulls = df_imputed[feat].isna().sum()
            if remaining_nulls > 0:
                logger.warning(
                    f"Sector-median imputation left {remaining_nulls} NaNs for '{feat}'. "
                    f"Applying global-median safety fallback."
                )
                global_median = df_imputed[feat].median()
                df_imputed[feat] = df_imputed[feat].fillna(global_median)

            logger.info(f"Imputed missing values for '{feat}'. Remaining NaNs: 0")

    return df_imputed


def prepare_features(df: pd.DataFrame) -> tuple[np.ndarray, StandardScaler]:
    """
    Extracts the feature matrix X, runs assertions, and normalizes using StandardScaler.
    """
    features = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]

    X = df[features].copy()

    # Assertions to verify constraints
    assert len(X) == 92, f"Expected 92 companies, got {len(X)}"
    assert (
        X.isna().sum().sum() == 0
    ), f"Detected missing values in feature matrix X:\n{X.isna().sum()}"

    logger.info(
        "Feature matrix validations passed (92 rows, 0 NaNs). Applying StandardScaler."
    )

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, scaler


def generate_elbow_plot(X_scaled: np.ndarray) -> None:
    """
    Performs elbow analysis for k=2..10 and saves the plot to reports/elbow_plot.png.
    """
    k_range = list(range(2, 11))
    inertias = []

    logger.info("Executing KMeans elbow analysis for k=2..10...")
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto")
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
        logger.info(f"k={k} | Inertia={kmeans.inertia_:.4f}")

    # Plot setting
    plt.figure(figsize=(8, 5))
    plt.plot(k_range, inertias, marker="o", linestyle="-", color="#1f77b4")
    plt.title("KMeans Elbow Plot: Financial Ratios Clustering")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia (Within-Cluster Sum of Squares)")
    plt.xticks(k_range)
    plt.grid(True, linestyle="--", alpha=0.6)

    reports_dir = BASE_DIR / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    plot_path = reports_dir / "elbow_plot.png"

    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close()
    logger.info(f"Elbow plot saved successfully to: {plot_path}")


def run_kmeans(X_scaled: np.ndarray) -> tuple[np.ndarray, np.ndarray, KMeans]:
    """
    Trains final KMeans model (k=5) and calculates distance from centroid for each company.
    """
    logger.info("Training final KMeans model (k=5, random_state=42)...")

    kmeans = KMeans(n_clusters=5, random_state=42, n_init="auto")
    cluster_ids = kmeans.fit_predict(X_scaled)

    centroids = kmeans.cluster_centers_
    distances = []
    for i, x in enumerate(X_scaled):
        centroid = centroids[cluster_ids[i]]
        dist = np.linalg.norm(x - centroid)
        distances.append(round(float(dist), 4))

    return cluster_ids, np.array(distances), kmeans


def assign_cluster_names(df: pd.DataFrame, kmeans: KMeans) -> pd.DataFrame:
    """
    Assigns descriptive names to each cluster dynamically based on their centroids.

    Archetype rules:
    - Highest debt_to_equity: Highly Leveraged Financials & Utilities
    - Highest return_on_equity_pct: Capital-Efficient Outliers (High ROE)
    - Highest operating_profit_margin_pct (among remaining): High-Quality Cash Compounders
    - Highest revenue_cagr_5yr (among remaining): Emerging Growth Leaders
    - Last remaining: Stable Blue Chips & Defensives
    """
    features = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]

    # Calculate feature averages for each cluster
    cluster_means = df.groupby("cluster_id")[features].mean()

    logger.info(
        "Computing centroid means in original feature space to assign archetype names:"
    )

    cluster_names = {}
    unassigned = set(range(5))

    # 1. Highest D/E -> Highly Leveraged Financials & Utilities
    highest_de_cid = cluster_means["debt_to_equity"].idxmax()
    cluster_names[highest_de_cid] = "Highly Leveraged Financials & Utilities"
    unassigned.remove(highest_de_cid)
    logger.info(
        f"Cluster {highest_de_cid} mapped to 'Highly Leveraged Financials & Utilities' (Mean D/E: {cluster_means.loc[highest_de_cid, 'debt_to_equity']:.2f})"
    )

    # 2. Highest ROE -> Capital-Efficient Outliers (High ROE)
    roe_means = cluster_means.loc[list(unassigned), "return_on_equity_pct"]
    highest_roe_cid = roe_means.idxmax()
    cluster_names[highest_roe_cid] = "Capital-Efficient Outliers (High ROE)"
    unassigned.remove(highest_roe_cid)
    logger.info(
        f"Cluster {highest_roe_cid} mapped to 'Capital-Efficient Outliers (High ROE)' (Mean ROE: {cluster_means.loc[highest_roe_cid, 'return_on_equity_pct']:.2f})"
    )

    # 3. Highest OPM among remaining -> High-Quality Cash Compounders
    opm_means = cluster_means.loc[list(unassigned), "operating_profit_margin_pct"]
    highest_opm_cid = opm_means.idxmax()
    cluster_names[highest_opm_cid] = "High-Quality Cash Compounders"
    unassigned.remove(highest_opm_cid)
    logger.info(
        f"Cluster {highest_opm_cid} mapped to 'High-Quality Cash Compounders' (Mean OPM: {cluster_means.loc[highest_opm_cid, 'operating_profit_margin_pct']:.2f}%)"
    )

    # 4. Highest Revenue CAGR among remaining -> Emerging Growth Leaders
    rev_means = cluster_means.loc[list(unassigned), "revenue_cagr_5yr"]
    highest_rev_cid = rev_means.idxmax()
    cluster_names[highest_rev_cid] = "Emerging Growth Leaders"
    unassigned.remove(highest_rev_cid)
    logger.info(
        f"Cluster {highest_rev_cid} mapped to 'Emerging Growth Leaders' (Mean 5Y Rev CAGR: {cluster_means.loc[highest_rev_cid, 'revenue_cagr_5yr']:.2f}%)"
    )

    # 5. Last remaining -> Stable Blue Chips & Defensives
    last_cid = next(iter(unassigned))
    cluster_names[last_cid] = "Stable Blue Chips & Defensives"
    logger.info(
        f"Cluster {last_cid} mapped to 'Stable Blue Chips & Defensives' (Mean 5Y Rev CAGR: {cluster_means.loc[last_cid, 'revenue_cagr_5yr']:.2f}%, Mean D/E: {cluster_means.loc[last_cid, 'debt_to_equity']:.2f})"
    )

    df_named = df.copy()
    df_named["cluster_name"] = df_named["cluster_id"].map(cluster_names)

    return df_named


def save_cluster_labels(df: pd.DataFrame) -> None:
    """
    Saves the final cluster labels and distances to output/cluster_labels.csv.
    """
    output_dir = OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    labels_file = output_dir / "cluster_labels.csv"

    cols_to_save = [
        "company_id",
        "cluster_id",
        "cluster_name",
        "distance_from_centroid",
    ]
    df[cols_to_save].to_csv(labels_file, index=False)

    logger.info(f"Cluster labels successfully saved to: {labels_file}")


def main() -> None:
    """
    Orchestrator for the clustering pipeline.
    """
    logger.info("=========================================")
    logger.info("Starting KMeans Financial Clustering Engine")
    logger.info("=========================================")

    try:
        # Load and clean
        df_raw = load_clustering_data()
        df_imputed = impute_sector_medians(df_raw)

        # Scale
        X_scaled, _scaler = prepare_features(df_imputed)

        # Elbow analysis
        generate_elbow_plot(X_scaled)

        # Run KMeans
        cluster_ids, distances, kmeans = run_kmeans(X_scaled)

        # Add labels to dataframe
        df_imputed["cluster_id"] = cluster_ids
        df_imputed["distance_from_centroid"] = distances

        # Assign cluster names
        df_final = assign_cluster_names(df_imputed, kmeans)

        # Export labels
        save_cluster_labels(df_final)

        # Print cluster counts and summaries
        logger.info("\nCluster Distribution Summary:")
        counts = df_final["cluster_name"].value_counts()
        for name, count in counts.items():
            logger.info(f"- {name}: {count} companies")

        # Validations
        assert (
            df_final["company_id"].nunique() == 92
        ), f"Validation failed: expected 92 unique companies, got {df_final['company_id'].nunique()}"
        assert (
            df_final["cluster_id"].nunique() == 5
        ), f"Validation failed: expected 5 clusters, got {df_final['cluster_id'].nunique()}"
        assert (
            df_final["cluster_name"].isna().sum() == 0
        ), "Validation failed: detected null cluster names"
        assert (
            df_final["distance_from_centroid"].isna().sum() == 0
        ), "Validation failed: detected null distances"

        logger.info("All output validations passed successfully.")
        logger.info("=========================================")
        logger.info("KMeans Financial Clustering Completed Successfully")
        logger.info("=========================================")

    except Exception as e:
        logger.error(f"Clustering pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
