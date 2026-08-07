"""
Financial Ratio Distribution Generator.
Generates multi-panel histogram and outlier distribution charts for evaluated KPIs.
Saves visual artifacts to reports/profitability_distribution.png and README_ASSETS/.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.utils.logger import get_logger

logger = get_logger("ratio_visualizer")


def generate_profitability_charts(csv_log_path: Path, output_dir: Path) -> Path:
    """Generate and save multi-panel ratio distribution plots."""
    if not csv_log_path.exists():
        logger.error(f"Ratio calculation log CSV not found at {csv_log_path}")
        raise FileNotFoundError(f"{csv_log_path} missing")

    df = pd.read_csv(csv_log_path)
    df_clean = df[df["status"] == "VALID"].copy()
    df_clean["value"] = pd.to_numeric(df_clean["value"], errors="coerce")

    # Set aesthetic style
    sns.set_theme(style="whitegrid", palette="muted")
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(
        "Nifty 100 Financial Profitability Ratio Distributions",
        fontsize=18,
        fontweight="bold",
        y=0.98,
    )

    ratios = ["NPM", "OPM", "ROE", "ROCE", "ROA"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    for i, ratio in enumerate(ratios):
        row, col = divmod(i, 3)
        ax = axes[row, col]
        sub = df_clean[df_clean["ratio_name"] == ratio]["value"].dropna()

        # Trim extreme display outliers for visualization clarity
        q_low, q_high = sub.quantile(0.02), sub.quantile(0.98)
        trimmed = sub[(sub >= q_low) & (sub <= q_high)]

        sns.histplot(
            trimmed,
            kde=True,
            ax=ax,
            color=colors[i],
            bins=30,
            edgecolor="black",
            alpha=0.6,
        )
        mean_val = trimmed.mean()
        median_val = trimmed.median()

        ax.axvline(
            mean_val,
            color="red",
            linestyle="--",
            linewidth=1.5,
            label=f"Mean: {mean_val:.1f}%",
        )
        ax.axvline(
            median_val,
            color="green",
            linestyle="-.",
            linewidth=1.5,
            label=f"Median: {median_val:.1f}%",
        )

        ax.set_title(
            f"{ratio} Distribution (96% Central Trimmed)",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_xlabel("Percentage (%)", fontsize=11)
        ax.set_ylabel("Frequency", fontsize=11)
        ax.legend(fontsize=10)

    # 6th Subplot: Boxplot Summary
    ax_box = axes[1, 2]
    # Filter reasonable bounds for combined boxplot
    df_box = df_clean[df_clean["ratio_name"].isin(ratios)].copy()
    df_box = df_box[(df_box["value"] >= -50) & (df_box["value"] <= 150)]
    sns.boxplot(
        data=df_box,
        x="ratio_name",
        y="value",
        ax=ax_box,
        hue="ratio_name",
        palette="muted",
        legend=False,
    )
    ax_box.set_title(
        "Cross-KPI Outlier & Quartile Range Comparison", fontsize=13, fontweight="bold"
    )
    ax_box.set_xlabel("KPI Metric", fontsize=11)
    ax_box.set_ylabel("Percentage (%)", fontsize=11)

    plt.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "profitability_distribution.png"
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()

    # Also save copy to README_ASSETS
    assets_dir = BASE_DIR / "README_ASSETS"
    assets_dir.mkdir(parents=True, exist_ok=True)
    plt_asset = assets_dir / "profitability_distribution.png"
    import shutil

    shutil.copy(out_file, plt_asset)

    logger.info(f"Profitability distribution chart saved to {out_file} and {plt_asset}")
    return out_file


if __name__ == "__main__":
    log_csv = BASE_DIR / "output" / "ratio_calculation_log.csv"
    out_reports = BASE_DIR / "reports"
    chart_path = generate_profitability_charts(log_csv, out_reports)
    print(f"[+] Visual ratio distribution chart generated successfully: {chart_path}")
