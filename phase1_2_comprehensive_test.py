from pathlib import Path
# -*- coding: utf-8 -*-
"""
Phase 1-2 Comprehensive Test Script
"""
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

import os
os.chdir(str(Path(__file__).resolve().parent))

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
        else:
            print("[FAIL] Data is empty")
            return False
        
        # Test BTCUSDT 1d with limit=1
        print("\n--- BTCUSDT 1d (limit=1) ---")
        df_1d = provider.get_ohlcv("BTCUSDT", "1d", limit=1)
        if not df_1d.empty:
            print(f"[OK] Got {len(df_1d)} records")
        else:
            print("[FAIL] Data is empty")
            return False
        
        # Test BTCUSDT 1d with limit=1000
        print("\n--- BTCUSDT 1d (limit=1000) ---")
        df_1d_1000 = provider.get_ohlcv("BTCUSDT", "1d", limit=1000)
        if not df_1d_1000.empty:
            print(f"[OK] Got {len(df_1d_1000)} records")
            first_date = df_1d_1000.iloc[0]['datetime']
            last_date = df_1d_1000.iloc[-1]['datetime']
            print(f"   Date range: {first_date} to {last_date}")
        else:
            print("[FAIL] Data is empty")
            return False
        
        return True
    except Exception as e:
        print(f"[FAIL] Binance provider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_yahoo_finance_provider():
    """Test Yahoo Finance provider with backup sources"""
    print("\n" + "="*60)
    print("[TEST 2] Yahoo Finance provider (with backup sources) Test")
    print("="*60)
    
    try:
        from data.providers.us_market_provider import USMarketProvider
        
        provider = USMarketProvider()
        
        # Test NASDAQ
        print("\n--- NASDAQ Data ---")
        nasdaq_data = provider.get_nasdaq_data()
        if nasdaq_data:
            print(f"[OK] Got NASDAQ data")
            print(f"   Price: {nasdaq_data['price']}")
            print(f"   Change: {nasdaq_data['change_percent']:.2f}%")
            print(f"   Source: {nasdaq_data['source']}")
        else:
            print("[FAIL] Failed to get NASDAQ data")
        
        # Test S&P 500
        print("\n--- S&P 500 Data ---")
        sp500_data = provider.get_sp500_data()
        if sp500_data:
            print(f"[OK] Got S&P 500 data")
            print(f"   Price: {sp500_data['price']}")
            print(f"   Change: {sp500_data['change_percent']:.2f}%")
            print(f"   Source: {sp500_data['source']}")
        else:
            print("[FAIL] Failed to get S&P 500 data")
        
        # Test USDCNY
        print("\n--- USDCNY Rate ---")
        usdcny_data = provider.get_usdcny_rate()
        if usdcny_data:
            print(f"[OK] Got USDCNY rate")
            print(f"   Rate: {usdcny_data['rate']}")
            print(f"   Source: {usdcny_data['source']}")
        else:
            print("[FAIL] Failed to get USDCNY rate")
        
        return nasdaq_data is not None or sp500_data is not None or usdcny_data is not None
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
        
        # Time range
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM kline_data_1d")
        min_dt, max_dt = cursor.fetchone()
        print(f"\nTime range: {min_dt} to {max_dt}")
        
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
        cursor.execute("SELECT symbol, price, change_percent, data_timestamp, source FROM us_market_index ORDER BY data_timestamp DESC")
        rows = cursor.fetchall()
        print(f"\nData:")
        for row in rows:
            print(f"   {row}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"[FAIL] us_market_index check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_backtrader():
    """Check if Backtrader can load data from database"""
    print("\n" + "="*60)
    print("[TEST 5] Backtrader Data Loading Test")
    print("="*60)
    
    try:
        import backtrader as bt
        import pandas as pd
        from data.providers.binance_provider import BinanceDataProvider
        
        provider = BinanceDataProvider()
        
        # Get BTCUSDT 1d data
        print("\n--- Loading BTCUSDT 1d data ---")
        df = provider.get_ohlcv("BTCUSDT", "1d", limit=500)
        if df.empty:
            print("[FAIL] No data returned")
            return False
        
        print(f"[OK] Loaded {len(df)} records")
        print(f"   Date range: {df.iloc[0]['datetime']} to {df.iloc[-1]['datetime']}")
        
        # Create Backtrader data feed
        print("\n--- Creating Backtrader data feed ---")
        df_bt = df.copy()
        if "symbol" in df_bt.columns:
            df_bt = df_bt.drop(columns=["symbol"])
        
        data = bt.feeds.PandasData(dataname=df_bt)
        
        # Create Cerebro
        cerebro = bt.Cerebro()
        cerebro.adddata(data)
        cerebro.broker.setcash(100000)
        
        print(f"[OK] Cerebro created with {len(cerebro.datas)} data feeds")
        print(f"   Initial cash: {cerebro.broker.getcash()}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Backtrader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("="*60)
    print("QuantTradeSys Phase 1-2 Comprehensive Test")
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
    
    # Test 5: Backtrader
    results['backtrader'] = check_backtrader()
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    for test_name, result in results.items():
        status = "[OK] Pass" if result else "[FAIL]"
        print(f"   {test_name}: {status}")
    
    # Overall result
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED!")
    print("="*60)
