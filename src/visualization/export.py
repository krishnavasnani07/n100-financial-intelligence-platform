"""
Bulk Chart Export Utility.
Initializes visual folders and exports default charts (radar, trends, heatmaps).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from src.config.settings import DB_PATH, OUTPUT_DIR
from src.utils.logger import get_logger
from src.visualization.charts import generate_trend_charts
from src.visualization.heatmaps import generate_sector_heatmap
from src.visualization.radar_chart import (generate_peer_radar,
                                           generate_single_radar)

logger = get_logger("chart_exporter")


def export_all_charts(
    db_path: Optional[Path] = None, output_dir: Optional[Path] = None
) -> None:
    """
    Creates chart output directories and exports standard charts for key companies and sectors.
    """
    db_file = db_path or DB_PATH
    out_dir = output_dir or OUTPUT_DIR

    # 1. Initialize subdirectories
    chart_dirs = {
        "radar": out_dir / "charts" / "radar",
        "peer": out_dir / "charts" / "peer",
        "trends": out_dir / "charts" / "trends",
        "heatmaps": out_dir / "charts" / "heatmaps",
    }

    for folder in chart_dirs.values():
        folder.mkdir(parents=True, exist_ok=True)

    logger.info("Visual directories successfully initialized.")

    # 2. Query sectors and companies to build dynamically
    conn = sqlite3.connect(str(db_file))
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT broad_sector FROM sectors WHERE broad_sector IS NOT NULL"
        )
        sectors = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT company_id FROM financial_ratios")
        companies = [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

    logger.info(
        f"Loaded {len(sectors)} sectors and {len(companies)} companies from database."
    )

    # 3. Export Single Company Radars and Trends for a subset of prominent companies
    default_companies = ["INFY", "TCS", "HDFCBANK", "RELIANCE", "LT"]
    # Filter to only companies that exist in our database
    valid_defaults = [c for c in default_companies if c in companies]

    for cid in valid_defaults:
        try:
            radar_path = chart_dirs["radar"] / f"{cid}_radar.png"
            generate_single_radar(cid, save_path=radar_path, db_path=db_file)
            logger.info(f"Generated single radar chart for {cid}")

            trend_path = chart_dirs["trends"] / f"{cid}_trends.png"
            generate_trend_charts(cid, save_path=trend_path, db_path=db_file)
            logger.info(f"Generated trend charts for {cid}")
        except Exception as e:
            logger.error(f"Failed to generate charts for {cid}: {e}")

    # 4. Export Peer Comparison Radar
    peer_pairs = [("INFY", "TCS"), ("RELIANCE", "LT")]
    for c1, c2 in peer_pairs:
        if c1 in companies and c2 in companies:
            try:
                peer_path = chart_dirs["peer"] / f"{c1}_vs_{c2}_radar.png"
                generate_peer_radar(c1, c2, save_path=peer_path, db_path=db_file)
                logger.info(f"Generated peer comparison radar for {c1} vs {c2}")
            except Exception as e:
                logger.error(f"Failed to generate peer radar for {c1} vs {c2}: {e}")

    # 5. Export Sector Heatmaps
    for sector in sectors:
        try:
            sec_filename = (
                sector.lower().replace(" ", "_").replace("-", "_") + "_heatmap.png"
            )
            sec_path = chart_dirs["heatmaps"] / sec_filename
            generate_sector_heatmap(sector, save_path=sec_path, db_path=db_file)
            logger.info(f"Generated heatmap for sector: {sector}")
        except Exception as e:
            logger.error(f"Failed to generate heatmap for sector '{sector}': {e}")

    logger.info("All chart exports finished successfully.")


if __name__ == "__main__":
    export_all_charts()
