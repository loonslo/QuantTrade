"""
用户策略模板
演示如何创建自定义策略，专注于核心交易逻辑
"""

import pandas as pd
from typing import Optional
from strategies.base.simple_strategy_base import SimpleStrategyBase
from core.strategy_interface import Signal, StrategyContext


class UserStrategyTemplate(SimpleStrategyBase):
    """
    用户策略模板
    继承SimpleStrategyBase，只需要实现generate_signal方法
    """
    
    def __init__(self, name: str = "user_strategy", params: Optional[dict] = None):
        """
        初始化策略
        
        Args:
            name: 策略名称
            params: 策略参数
        """
        default_params = {
            # 在这里定义你的策略参数
            'ma_period': 20,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'volume_threshold': 1000
        }
        
        if params:
            default_params.update(params)
        
        super().__init__(name, default_params)
    
    def generate_signal(self, data: pd.DataFrame, context: StrategyContext) -> Optional[Signal]:
        """
        生成交易信号 - 这是你需要实现的核心方法
        
        Args:
            data: K线数据 DataFrame，包含 open, high, low, close, volume 等列
            context: 策略上下文，包含当前资金、交易对等信息
            
        Returns:
            Optional[Signal]: 交易信号，如果没有信号则返回None
        """
        try:
            # 检查数据长度是否足够
            if len(data) < max(self.params['ma_period'], self.params['rsi_period']):
                return None
            
            # 获取当前价格和时间
            current_price = data['close'].iloc[-1]
            current_time = data['datetime'].iloc[-1] if 'datetime' in data.columns else None
            
            # 计算技术指标
            sma = self.calculate_sma(data['close'], self.params['ma_period']).iloc[-1]
            rsi = self.calculate_rsi(data['close'], self.params['rsi_period']).iloc[-1]
            
            # 检查指标是否有效
            if pd.isna(sma) or pd.isna(rsi):
                return None
            
            # ========== 在这里实现你的策略逻辑 ==========
            
            # 示例策略逻辑：
            # 1. RSI超卖 + 价格在均线下方 = 买入信号
            if (rsi < self.params['rsi_oversold'] and 
                current_price < sma):
                return self.create_signal(
                    symbol=context.symbol,
                    signal_type='buy',
                    price=current_price,
                    datetime=current_time,
                    strength=0.9
                )
            
            # 2. RSI超买 + 价格在均线上方 = 卖出信号
            elif (rsi > self.params['rsi_overbought'] and 
                  current_price > sma):
                return self.create_signal(
                    symbol=context.symbol,
                    signal_type='sell',
                    price=current_price,
                    datetime=current_time,
                    strength=0.9
                )
            
            # 3. 价格突破均线 = 买入信号
            elif current_price > sma * 1.01:  # 1%突破
                return self.create_signal(
                    symbol=context.symbol,
                    signal_type='buy',
                    price=current_price,
                    datetime=current_time,
                    strength=0.8
                )
            
            # 4. 价格跌破均线 = 卖出信号
            elif current_price < sma * 0.99:  # 1%跌破
                return self.create_signal(
                    symbol=context.symbol,
                    signal_type='sell',
                    price=current_price,
                    datetime=current_time,
                    strength=0.8
                )
            
            # ========== 策略逻辑结束 ==========
            
            return None
            
        except Exception as e:
            self.logger.error(f"生成信号失败: {e}")
            return None


# 使用示例
if __name__ == "__main__":
    # 创建策略实例
    strategy = UserStrategyTemplate(
        name="my_custom_strategy",
        params={
            'ma_period': 20,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70
        }
    )
    
    print(f"策略名称: {strategy.name}")
    print(f"策略参数: {strategy.params}") 