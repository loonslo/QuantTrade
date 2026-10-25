import os
from pathlib import Path
import sqlite3
conn = sqlite3.connect(os.getenv('DB_PATH', str(Path(__file__).resolve().parent / 'quant_trading.db')))
cursor = conn.cursor()

# Check kline_data_1d schema
print("=== kline_data_1d schema ===")
cursor.execute("PRAGMA table_info(kline_data_1d)")
for row in cursor.fetchall():
    print(row)

print("\n=== kline_data_1d sample ===")
cursor.execute("SELECT * FROM kline_data_1d LIMIT 3")
for row in cursor.fetchall():
    print(row)

# Check us_market_index schema
print("\n=== us_market_index schema ===")
cursor.execute("PRAGMA table_info(us_market_index)")
for row in cursor.fetchall():
    print(row)

print("\n=== us_market_index sample ===")
cursor.execute("SELECT * FROM us_market_index LIMIT 3")
for row in cursor.fetchall():
    print(row)

conn.close()
