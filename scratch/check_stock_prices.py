import sqlite3
import pandas as pd

conn = sqlite3.connect("db/nifty100.db")
df = pd.read_sql_query("SELECT * FROM stock_prices LIMIT 10", conn)
print("Stock Prices Sample:")
print(df)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM stock_prices")
print("Total rows in stock_prices:", cursor.fetchone()[0])

cursor.execute("SELECT DISTINCT date FROM stock_prices ORDER BY date DESC LIMIT 10")
print("Distinct dates:", cursor.fetchall())
conn.close()
