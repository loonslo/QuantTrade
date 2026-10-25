import os
from pathlib import Path
import sqlite3
conn = sqlite3.connect(os.getenv('DB_PATH', str(Path(__file__).resolve().parent / 'quant_trading.db')))
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

# Check kline_data_1d table
if 'kline_data_1d' in tables:
    cursor.execute("SELECT COUNT(*) FROM kline_data_1d")
    count = cursor.fetchone()[0]
    print(f"kline_data_1d count: {count}")
    
    cursor.execute("SELECT * FROM kline_data_1d LIMIT 5")
    rows = cursor.fetchall()
    print(f"Sample rows from kline_data_1d:")
    for row in rows:
        print(row)

# Check us_market_index table
if 'us_market_index' in tables:
    cursor.execute("SELECT COUNT(*) FROM us_market_index")
    count = cursor.fetchone()[0]
    print(f"us_market_index count: {count}")
    
    cursor.execute("SELECT * FROM us_market_index LIMIT 5")
    rows = cursor.fetchall()
    print(f"Sample rows from us_market_index:")
    for row in rows:
        print(row)

conn.close()
