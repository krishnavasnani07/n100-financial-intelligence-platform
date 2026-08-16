import sys
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from src.config.settings import DB_PATH
except ImportError:
    DB_PATH = Path("data/nifty100.db")


def check_integrity(conn):
    print("\nDatabase Integrity & Health Check:")
    print("==================================")
    
    # 1. Integrity check
    try:
        integrity = conn.execute("PRAGMA integrity_check;").fetchone()[0]
        print(f"Integrity Check: {integrity}")
    except Exception as e:
        print(f"Integrity Check Failed: {e}", file=sys.stderr)
        
    # 2. Foreign key check
    try:
        fk_violations = conn.execute("PRAGMA foreign_key_check;").fetchall()
        if not fk_violations:
            print("Foreign Key Check: OK (0 violations)")
        else:
            print(f"Foreign Key Violations Found: {len(fk_violations)} violations!", file=sys.stderr)
            for v in fk_violations:
                print(f"  Table: {v[0]}, RowId: {v[1]}, Parent Table: {v[2]}, Fk Index: {v[3]}", file=sys.stderr)
    except Exception as e:
        print(f"Foreign Key Check Failed: {e}", file=sys.stderr)


def get_table_stats(conn):
    print("\nTable Statistics:")
    print("=================")
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [r[0] for r in cursor.fetchall()]
    
    if not tables:
        print("No tables found in the database.")
        return

    # Print table header
    print(f"{'Table Name':<25} | {'Record Count':<12}")
    print("-" * 40)
    
    total_records = 0
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table:<25} | {count:<12}")
            total_records += count
        except Exception as e:
            print(f"{table:<25} | Error: {e}")
            
    print("-" * 40)
    print(f"{'Total Records':<25} | {total_records:<12}")


def main():
    print(f"Connecting to database at: {DB_PATH}")
    if not DB_PATH.exists():
        print(f"Error: Database file does not exist.", file=sys.stderr)
        sys.exit(1)
        
    try:
        conn = sqlite3.connect(DB_PATH)
        get_table_stats(conn)
        check_integrity(conn)
        conn.close()
    except Exception as e:
        print(f"Error connecting/querying database: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
