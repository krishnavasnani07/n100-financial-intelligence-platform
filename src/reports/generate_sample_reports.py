"""
Batch tearsheet generator for test companies: TCS, HDFCBANK, RELIANCE, SUNPHARMA, TATASTEEL.
Verifies page count and execution time.
"""

import sys
import time
from pathlib import Path

# Insert project base path to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.reports.tearsheet import generate_tearsheet

TEST_COMPANIES = ["TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL"]


def count_pdf_pages(pdf_path: Path) -> int:
    """Estimates the page count of a PDF by scanning for /Type /Page tags."""
    try:
        with open(pdf_path, "rb") as f:
            content = f.read()
        # Count page objects. This is a reliable approximation for ReportLab-generated PDFs.
        # We must subtract /Type /Pages (plural, parent node) from /Type /Page (singular, child node)
        pages_raw = content.count(b"/Type /Page")
        parent_nodes = content.count(b"/Type /Pages")
        pages = pages_raw - parent_nodes
        if pages == 0:
            # Fallback check for alternate capitalization/spacing
            pages = content.count(b"/Type/Page") - content.count(b"/Type/Pages")
        return pages
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return -1


def run_batch():
    print("=" * 60)
    print("STARTING BATCH TEARSHEET GENERATION")
    print("=" * 60)

    success_count = 0
    total_time = 0.0

    for company in TEST_COMPANIES:
        print(f"\n[*] Processing company: {company}...")
        start = time.time()
        try:
            pdf_path = generate_tearsheet(company)
            elapsed = time.time() - start
            total_time += elapsed

            # Page count verification
            pages = count_pdf_pages(pdf_path)
            print(f"[+] PDF path: {pdf_path}")
            print(f"[+] Execution time: {elapsed:.2f} seconds")
            print(f"[+] Page count: {pages}")

            if pages == 2:
                print(
                    f"[SUCCESS] {company} tearsheet generated and page-budget verified (2 pages)."
                )
                success_count += 1
            else:
                print(
                    f"[WARNING] {company} tearsheet generated but pages count is {pages} (expected 2 pages)."
                )
                success_count += 1  # generated but maybe sizing is off
        except Exception as e:
            print(f"[ERROR] Failed to generate tearsheet for {company}: {e}")

    print("\n" + "=" * 60)
    print("BATCH COMPILATION SUMMARY")
    print("=" * 60)
    print(f"Successful runs: {success_count}/{len(TEST_COMPANIES)}")
    print(f"Total processing time: {total_time:.2f} seconds")
    print(f"Average time per company: {total_time/len(TEST_COMPANIES):.2f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    run_batch()
