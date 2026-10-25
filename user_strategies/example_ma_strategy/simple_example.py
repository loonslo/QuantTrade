#!/usr/bin/env python3
"""
简化策略使用示例
演示如何使用SimpleStrategyBase创建和运行自定义策略
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from user_strategies.example_ma_strategy.simple_strategy import SimpleMAStrategy
from strategies.simple_strategy_runner import run_simple_strategy


def create_sample_data(days: int = 100) -> pd.DataFrame:
    """
    创建示例数据
    
    Args:
        days: 数据天数
        
    Returns:
        pd.DataFrame: 示例K线数据
    """
    # 创建时间序列
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='1H')
    
    # 创建模拟价格数据
    np.random.seed(42)  # 确保可重复性
    base_price = 50000.0
    price_changes = np.random.normal(0, 0.02, len(dates))  # 2%标准差
    prices = [base_price]
    
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    # 创建DataFrame
    data = pd.DataFrame({
        'datetime': dates,
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': np.random.uniform(100, 1000, len(dates))
    })
    
    return data


def main():
    """主函数"""
    print("="*50)
    print("简化策略使用示例")
    print("="*50)
    
    # 1. 创建示例数据
    print("1. 创建示例数据...")
    data = create_sample_data(30)  # 30天数据
    print(f"   数据长度: {len(data)} 条记录")
    print(f"   时间范围: {data['datetime'].min()} 到 {data['datetime'].max()}")
    
    # 2. 创建策略实例
    print("\n2. 创建策略实例...")
    strategy = SimpleMAStrategy(
        name="my_ma_strategy",
        params={
            'sma_period': 20,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
    )
    print(f"   策略名称: {strategy.name}")
    print(f"   策略参数: {strategy.params}")
    
    # 3. 运行策略
    print("\n3. 运行策略...")
    signals = run_simple_strategy(
        strategy=strategy,
        data=data,
        symbol="BTC/USDT",
        initial_cash=10000.0
    )
    
    # 4. 显示结果
    print("\n4. 策略结果:")
    print(f"   生成信号数量: {len(signals)}")
    
    if signals:
        print("\n   信号详情:")
        for i, signal in enumerate(signals[:5]):  # 只显示前5个信号
            print(f"   {i+1}. {signal.signal_type} {signal.symbol} "
                  f"价格: {signal.price:.2f} 强度: {signal.strength:.2f} "
                  f"时间: {signal.datetime}")
        
        if len(signals) > 5:
            print(f"   ... 还有 {len(signals) - 5} 个信号")
    
    print("\n" + "="*50)
    print("示例完成！")


if __name__ == "__main__":
    main() 