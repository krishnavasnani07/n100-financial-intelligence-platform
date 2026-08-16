import sys
import sqlite3
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from src.config.settings import DB_PATH
except ImportError:
    DB_PATH = Path("data/nifty100.db")

def print_table(headers, rows):
    # Compute column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val or "")))
            
    # Print header separator
    header_str = " | ".join(f"{str(h):<{widths[i]}}" for i, h in enumerate(headers))
    print(header_str)
    print("-+-".join("-" * w for w in widths))
    
    # Print rows
    for row in rows:
        row_str = " | ".join(f"{str(val or ''):<{widths[i]}}" for i, val in enumerate(row))
        print(row_str)

def main():
    parser = argparse.ArgumentParser(description="Query companies by broad sector.")
    parser.add_argument("sector", nargs="?", help="Broad sector name (e.g., 'IT Services', 'Utilities', 'Banking')")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if not args.sector:
        # List all sectors with company counts
        query = """
        SELECT s.broad_sector, COUNT(c.id) 
        FROM sectors s
        JOIN companies c ON s.company_id = c.id
        GROUP BY s.broad_sector
        ORDER BY COUNT(c.id) DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        print("\nAvailable Broad Sectors:")
        print("=========================")
        print_table(["Broad Sector", "Company Count"], rows)
        print("\nUsage: python scripts/query_sector_companies.py <SectorName>")
    else:
        # Query companies in the specific sector
        query = """
        SELECT c.id, c.company_name, s.sub_sector, s.market_cap_category
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        WHERE LOWER(s.broad_sector) = LOWER(?)
        ORDER BY c.id
        """
        cursor.execute(query, (args.sector,))
        rows = cursor.fetchall()
        
        if not rows:
            print(f"No companies found for sector: '{args.sector}'")
            print("Run without arguments to see available sectors.")
        else:
            print(f"\nCompanies in Broad Sector: '{args.sector}' (Total: {len(rows)})")
            print("=" * (30 + len(args.sector)))
            print_table(["Ticker", "Company Name", "Sub Sector", "Market Cap Cat"], rows)

    conn.close()

if __name__ == "__main__":
    main()
