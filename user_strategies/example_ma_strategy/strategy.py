"""
示例移动平均策略
演示如何使用策略系统
"""

import pandas as pd
from datetime import datetime
from typing import Optional
from strategies.base.simple_strategy_base import SimpleStrategyBase
from core.strategy_interface import Signal, StrategyContext


class ExampleMAStrategy(SimpleStrategyBase):
    """
    示例移动平均策略
    使用SimpleStrategyBase，专注于核心交易逻辑
    """
    
    def __init__(self, name: str = "example_ma_strategy", params: Optional[dict] = None):
        """
        初始化策略
        
        Args:
            name: 策略名称
            params: 策略参数
        """
        default_params = {
            'sma_period': 20,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
        
        if params:
            default_params.update(params)
        
        super().__init__(name, default_params)
    
    def generate_signal(self, data: pd.DataFrame, context: StrategyContext) -> Optional[Signal]:
        """
        生成交易信号
        
        Args:
            data: K线数据
            context: 策略上下文
            
        Returns:
            Optional[Signal]: 交易信号
        """
        try:
            # 检查数据长度
            if len(data) < self.params['sma_period']:
                return None
            
            # 获取当前价格
            current_price = data['close'].iloc[-1]
            current_time = data['datetime'].iloc[-1] if 'datetime' in data.columns else datetime.now()
            
            # 计算技术指标
            sma = self.calculate_sma(data['close'], self.params['sma_period']).iloc[-1]
            rsi = self.calculate_rsi(data['close'], self.params['rsi_period']).iloc[-1]
            
            # 检查指标是否有效
            if pd.isna(sma) or pd.isna(rsi):
                return None
            
            # 策略逻辑
            if rsi < self.params['rsi_oversold']:
                # RSI超卖，买入信号
                return self.create_signal(
                    symbol=context.symbol,
                    signal_type='buy',
                    price=current_price,
                    datetime=current_time,
                    strength=0.9
                )
            
            elif rsi > self.params['rsi_overbought']:
                # RSI超买，卖出信号
                return self.create_signal(
                    symbol=context.symbol,
                    signal_type='sell',
                    price=current_price,
                    datetime=current_time,
                    strength=0.9
                )
            
            elif current_price > sma:
                # 价格在均线上方，买入信号
                return self.create_signal(
                    symbol=context.symbol,
                    signal_type='buy',
                    price=current_price,
                    datetime=current_time,
                    strength=0.8
                )
            
            elif current_price < sma:
                # 价格在均线下方，卖出信号
                return self.create_signal(
                    symbol=context.symbol,
                    signal_type='sell',
                    price=current_price,
                    datetime=current_time,
                    strength=0.8
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"生成信号失败: {e}")
            return None


