import os
from pathlib import Path
import sqlite3
conn = sqlite3.connect(os.getenv('DB_PATH', str(Path(__file__).resolve().parent / 'quant_trading.db')))
cursor = conn.cursor()

# Check indexes on kline_data_1d
print("=== Indexes on kline_data_1d ===")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='kline_data_1d'")
for row in cursor.fetchall():
    if row[0]:
        print(row[0])
    else:
        print("(autoindex)")

print()

# Check for unique constraints
print("=== Table constraints ===")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='kline_data_1d'")
result = cursor.fetchone()
if result and result[0]:
    print(result[0])

print()

# Check us_market_index indexes
print("=== Indexes on us_market_index ===")
cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='us_market_index'")
for row in cursor.fetchall():
    if row[0]:
        print(row[0])
    else:
        print("(autoindex)")

print()

# Check for duplicates in kline_data_1d
print("=== Checking duplicates in kline_data_1d ===")
cursor.execute("""
    SELECT symbol, timeframe, timestamp, COUNT(*) as cnt 
    FROM kline_data_1d 
    GROUP BY symbol, timeframe, timestamp 
    HAVING cnt > 1
""")
duplicates = cursor.fetchall()
if duplicates:
    print(f"Found {len(duplicates)} duplicate entries:")
    for d in duplicates[:10]:
        print(f"  {d}")
else:
    print("No duplicates found")

print()

# Check for duplicates in us_market_index
print("=== Checking duplicates in us_market_index ===")
cursor.execute("""
    SELECT symbol, data_timestamp, COUNT(*) as cnt 
    FROM us_market_index 
    GROUP BY symbol, data_timestamp 
    HAVING cnt > 1
""")
duplicates = cursor.fetchall()
if duplicates:
    print(f"Found {len(duplicates)} duplicate entries:")
    for d in duplicates:
        print(f"  {d}")
else:
    print("No duplicates found")

conn.close()
