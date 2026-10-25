import os
from pathlib import Path
# -*- coding: utf-8 -*-
"""
Phase 1: Diagnosis and Verification Script
"""
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

import sqlite3
from datetime import datetime

def test_binance_provider():
    """Test Binance provider get_ohlcv"""
    print("\n" + "="*60)
    print("[TEST 1] Binance provider get_ohlcv Test")
    print("="*60)
    
    try:
        from data.providers.binance_provider import BinanceDataProvider
        
        provider = BinanceDataProvider()
        
        # Test BTCUSDT 1m with limit=1
        print("\n--- BTCUSDT 1m (limit=1) ---")
        df_1m = provider.get_ohlcv("BTCUSDT", "1m", limit=1)
        if not df_1m.empty:
            print(f"[OK] Got {len(df_1m)} records")
            print(f"   Latest data: {df_1m.iloc[-1].to_dict()}")
        else:
            print("[FAIL] Data is empty")
        
        # Test BTCUSDT 1d with limit=1
        print("\n--- BTCUSDT 1d (limit=1) ---")
        df_1d = provider.get_ohlcv("BTCUSDT", "1d", limit=1)
        if not df_1d.empty:
            print(f"[OK] Got {len(df_1d)} records")
            print(f"   Latest data: {df_1d.iloc[-1].to_dict()}")
        else:
            print("[FAIL] Data is empty")
        
        # Test BTCUSDT 1d with limit=1000
        print("\n--- BTCUSDT 1d (limit=1000) ---")
        df_1d_1000 = provider.get_ohlcv("BTCUSDT", "1d", limit=1000)
        if not df_1d_1000.empty:
            print(f"[OK] Got {len(df_1d_1000)} records")
            print(f"   Time range: {df_1d_1000['datetime'].min()} to {df_1d_1000['datetime'].max()}")
        else:
            print("[FAIL] Data is empty")
        
        return True
    except Exception as e:
        print(f"[FAIL] Binance provider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_yahoo_finance_provider():
    """Test Yahoo Finance provider"""
    print("\n" + "="*60)
    print("[TEST 2] Yahoo Finance provider Test")
    print("="*60)
    
    try:
        from data.providers.us_market_provider import USMarketProvider
        
        provider = USMarketProvider()
        
        # Test NASDAQ
        print("\n--- NASDAQ Data ---")
        nasdaq_data = provider.get_nasdaq_data()
        if nasdaq_data:
            print(f"[OK] Got NASDAQ data")
            print(f"   {nasdaq_data}")
        else:
            print("[FAIL] Failed to get NASDAQ data")
        
        # Test S&P 500
        print("\n--- S&P 500 Data ---")
        sp500_data = provider.get_sp500_data()
        if sp500_data:
            print(f"[OK] Got S&P 500 data")
            print(f"   {sp500_data}")
        else:
            print("[FAIL] Failed to get S&P 500 data")
        
        return True
    except Exception as e:
        print(f"[FAIL] Yahoo Finance provider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_database_kline_data():
    """Check kline_data_1d table in database"""
    print("\n" + "="*60)
    print("[TEST 3] Database kline_data_1d Table Check")
    print("="*60)
    
    try:
        conn = sqlite3.connect(os.getenv('DB_PATH', str(Path(__file__).resolve().parent / 'quant_trading.db')))
        cursor = conn.cursor()
        
        # Total count
        cursor.execute("SELECT COUNT(*) FROM kline_data_1d")
        total_count = cursor.fetchone()[0]
        print(f"\nTotal records: {total_count}")
        
        # Count by symbol
        cursor.execute("SELECT symbol, COUNT(*) FROM kline_data_1d GROUP BY symbol")
        symbol_counts = cursor.fetchall()
        print(f"\nBy symbol:")
        for symbol, count in symbol_counts:
            print(f"   {symbol}: {count} records")
        
        # Time range (using timestamp column)
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM kline_data_1d")
        min_dt, max_dt = cursor.fetchone()
        print(f"\nTime range: {min_dt} to {max_dt}")
        
        # Sample check (last 5)
        print("\nSample (last 5):")
        cursor.execute("SELECT * FROM kline_data_1d ORDER BY timestamp DESC LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f"   {row}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] Database check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_us_market_index():
    """Check us_market_index table"""
    print("\n" + "="*60)
    print("[TEST 4] Database us_market_index Table Check")
    print("="*60)
    
    try:
        conn = sqlite3.connect(os.getenv('DB_PATH', str(Path(__file__).resolve().parent / 'quant_trading.db')))
        cursor = conn.cursor()
        
        # Total count
        cursor.execute("SELECT COUNT(*) FROM us_market_index")
        total_count = cursor.fetchone()[0]
        print(f"\nTotal records: {total_count}")
        
        # Sample check
        cursor.execute("SELECT * FROM us_market_index ORDER BY data_timestamp DESC")
        rows = cursor.fetchall()
        print(f"\nAll data:")
        for row in rows:
            print(f"   {row}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] us_market_index check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*60)
    print("QuantTradeSys Phase 1: Diagnosis and Verification")
    print("="*60)
    
    results = {}
    
    # Test 1: Binance provider
    results['binance'] = test_binance_provider()
    
    # Test 2: Yahoo Finance provider
    results['yahoo'] = test_yahoo_finance_provider()
    
    # Test 3: Database kline_data_1d
    results['db_kline'] = check_database_kline_data()
    
    # Test 4: us_market_index
    results['db_us_market'] = check_us_market_index()
    
    print("\n" + "="*60)
    print("Phase 1 Diagnosis Results Summary")
    print("="*60)
    for test_name, result in results.items():
        status = "[OK] Pass" if result else "[FAIL]"
        print(f"   {test_name}: {status}")
