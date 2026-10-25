#!/usr/bin/env python3
"""
快速开始示例
演示如何使用简化的策略系统创建自定义策略
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from strategies.user_strategy_template import UserStrategyTemplate
from strategies.enhanced_strategy_runner import run_enhanced_strategy
from strategies.base.simple_strategy_base import SimpleStrategyBase
from core.strategy_interface import Signal, StrategyContext


class MyCustomStrategy(SimpleStrategyBase):
    """
    我的自定义策略
    只需要实现generate_signal方法即可
    """
    
    def __init__(self, name: str = "my_custom_strategy", params: dict = None):
        default_params = {
            'ma_short': 10,
            'ma_long': 30,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
        
        if params:
            default_params.update(params)
        
        super().__init__(name, default_params)
    
    def generate_signal(self, data: pd.DataFrame, context: StrategyContext) -> Signal:
        """
        生成交易信号 - 这是你需要实现的核心逻辑
        
        Args:
            data: K线数据
            context: 策略上下文
            
        Returns:
            Signal: 交易信号
        """
        try:
            # 检查数据长度
            if len(data) < self.params['ma_long']:
                return None
            
            # 获取当前价格
            current_price = data['close'].iloc[-1]
            current_time = data['datetime'].iloc[-1] if 'datetime' in data.columns else datetime.now()
            
            # 计算技术指标
            ma_short = self.calculate_sma(data['close'], self.params['ma_short']).iloc[-1]
            ma_long = self.calculate_sma(data['close'], self.params['ma_long']).iloc[-1]
            rsi = self.calculate_rsi(data['close'], self.params['rsi_period']).iloc[-1]
            
            # 检查指标是否有效
            if pd.isna(ma_short) or pd.isna(ma_long) or pd.isna(rsi):
                return None
            
            # ========== 你的策略逻辑 ==========
            
            # 策略1: 双均线金叉 + RSI超卖 = 强烈买入信号
            if (ma_short > ma_long and  # 短期均线上穿长期均线
                rsi < self.params['rsi_oversold']):  # RSI超卖
                return self.create_signal(
                    symbol=context.symbol,
                    signal_type='buy',
                    price=current_price,
                    datetime=current_time,
                    strength=0.95  # 高信号强度
                )
            
            # 策略2: 双均线死叉 + RSI超买 = 强烈卖出信号
            elif (ma_short < ma_long and  # 短期均线下穿长期均线
                  rsi > self.params['rsi_overbought']):  # RSI超买
                return self.create_signal(
                    symbol=context.symbol,
                    signal_type='sell',
                    price=current_price,
                    datetime=current_time,
                    strength=0.95  # 高信号强度
                )
            
            # 策略3: 价格突破短期均线 = 买入信号
            elif current_price > ma_short * 1.005:  # 0.5%突破
                return self.create_signal(
                    symbol=context.symbol,
                    signal_type='buy',
                    price=current_price,
                    datetime=current_time,
                    strength=0.7
                )
            
            # 策略4: 价格跌破短期均线 = 卖出信号
            elif current_price < ma_short * 0.995:  # 0.5%跌破
                return self.create_signal(
                    symbol=context.symbol,
                    signal_type='sell',
                    price=current_price,
                    datetime=current_time,
                    strength=0.7
                )
            
            # ========== 策略逻辑结束 ==========
            
            return None
            
        except Exception as e:
            self.logger.error(f"生成信号失败: {e}")
            return None


def create_sample_data(days: int = 60) -> pd.DataFrame:
    """创建示例数据"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='1H')
    
    # 创建模拟价格数据
    np.random.seed(42)
    base_price = 50000.0
    price_changes = np.random.normal(0, 0.015, len(dates))
    prices = [base_price]
    
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    data = pd.DataFrame({
        'datetime': dates,
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.008))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.008))) for p in prices],
        'close': prices,
        'volume': np.random.uniform(100, 1000, len(dates))
    })
    
    return data


def main():
    """主函数"""
    print("="*60)
    print("快速开始示例 - 自定义策略")
    print("="*60)
    
    # 1. 创建示例数据
    print("1. 创建示例数据...")
    data = create_sample_data(30)
    print(f"   数据长度: {len(data)} 条记录")
    print(f"   时间范围: {data['datetime'].min()} 到 {data['datetime'].max()}")
    
    # 2. 创建自定义策略
    print("\n2. 创建自定义策略...")
    strategy = MyCustomStrategy(
        name="my_custom_strategy",
        params={
            'ma_short': 10,
            'ma_long': 30,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
    )
    print(f"   策略名称: {strategy.name}")
    print(f"   策略参数: {strategy.params}")
    
    # 3. 运行策略
    print("\n3. 运行策略...")
    result = run_enhanced_strategy(
        strategy=strategy,
        data=data,
        symbol="BTC/USDT",
        initial_cash=10000.0,
        enable_analysis=True
    )
    
    # 4. 显示结果
    print("\n4. 策略结果:")
    signals = result['signals']
    print(f"   生成信号数量: {len(signals)}")
    
    if signals:
        print("\n   信号详情:")
        for i, signal in enumerate(signals[:5]):
            print(f"   {i+1}. {signal.signal_type} {signal.symbol} "
                  f"价格: {signal.price:.2f} 强度: {signal.strength:.2f} "
                  f"时间: {signal.datetime}")
        
        if len(signals) > 5:
            print(f"   ... 还有 {len(signals) - 5} 个信号")
    
    # 5. 显示性能分析
    if 'performance' in result:
        print("\n5. 性能分析:")
        perf = result['performance']
        print(f"   买入信号: {perf.get('buy_signals', 0)}")
        print(f"   卖出信号: {perf.get('sell_signals', 0)}")
        print(f"   买入比例: {perf.get('buy_ratio', 0):.2%}")
        
        if 'strength_stats' in perf:
            strength = perf['strength_stats']
            print(f"   平均信号强度: {strength.get('mean_strength', 0):.3f}")
            print(f"   强信号数量: {strength.get('strong_signals', 0)}")
            print(f"   弱信号数量: {strength.get('weak_signals', 0)}")
        
        if 'price_impact' in perf and perf['price_impact']:
            impact = perf['price_impact']
            print(f"   平均价格变化: {impact.get('mean_price_change', 0):.3%}")
            print(f"   正向变化: {impact.get('positive_changes', 0)}")
            print(f"   负向变化: {impact.get('negative_changes', 0)}")
    
    print("\n" + "="*60)
    print("示例完成！")
    print("\n如何使用:")
    print("1. 继承 SimpleStrategyBase")
    print("2. 实现 generate_signal 方法")
    print("3. 使用 run_enhanced_strategy 运行策略")
    print("4. 分析结果并优化策略")


if __name__ == "__main__":
    main() 