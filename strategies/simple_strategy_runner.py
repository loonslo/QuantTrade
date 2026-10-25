"""
简化策略运行器
提供简单的接口来调用自定义策略
"""

import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from core.strategy_interface import StrategyContext, Signal
from strategies.base.simple_strategy_base import SimpleStrategyBase
from utils.core.logger_manager import get_logger


class SimpleStrategyRunner:
    """
    简化策略运行器
    提供简单的接口来调用自定义策略
    """
    
    def __init__(self, strategy: SimpleStrategyBase, initial_cash: float = 10000.0):
        """
        初始化策略运行器
        
        Args:
            strategy: 策略实例
            initial_cash: 初始资金
        """
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.logger = get_logger("simple_runner")
        self.signals: List[Signal] = []
        self.context = None
    
    def run_strategy(self, data: pd.DataFrame, symbol: str = "BTC/USDT") -> List[Signal]:
        """
        运行策略
        
        Args:
            data: K线数据 DataFrame
            symbol: 交易对
            
        Returns:
            List[Signal]: 生成的信号列表
        """
        try:
            # 验证数据
            if not self.strategy.validate_data(data):
                return []
            
            # 创建策略上下文
            self.context = StrategyContext(
                initial_cash=self.initial_cash,
                symbol=symbol
            )
            
            self.logger.info(f"开始运行策略: {self.strategy.name}")
            self.logger.info(f"数据长度: {len(data)} 交易对: {symbol}")
            
            signals = []
            
            # 遍历每个K线数据
            for i in range(len(data)):
                # 获取当前K线数据
                current_data = data.iloc[:i+1]
                
                # 更新上下文时间
                if 'datetime' in current_data.columns:
                    self.context.current_time = current_data['datetime'].iloc[-1]
                else:
                    self.context.current_time = datetime.now()
                
                # 生成信号
                signal = self.strategy.generate_signal(current_data, self.context)
                
                if signal:
                    signals.append(signal)
                    self.strategy.log_signal(signal, current_data)
            
            self.signals = signals
            self.logger.info(f"策略运行完成，生成 {len(signals)} 个信号")
            
            return signals
            
        except Exception as e:
            self.logger.error(f"策略运行失败: {e}")
            return []
    
    def get_signal_summary(self) -> Dict[str, Any]:
        """获取信号摘要"""
        if not self.signals:
            return {}
        
        buy_signals = [s for s in self.signals if s.signal_type == 'buy']
        sell_signals = [s for s in self.signals if s.signal_type == 'sell']
        
        return {
            'total_signals': len(self.signals),
            'buy_signals': len(buy_signals),
            'sell_signals': len(sell_signals),
            'first_signal_time': self.signals[0].datetime if self.signals else None,
            'last_signal_time': self.signals[-1].datetime if self.signals else None
        }
    
    def print_summary(self) -> None:
        """打印运行摘要"""
        summary = self.get_signal_summary()
        
        if not summary:
            print("没有生成任何信号")
            return
        
        print("\n" + "="*40)
        print(f"策略: {self.strategy.name}")
        print("="*40)
        print(f"总信号数: {summary['total_signals']}")
        print(f"买入信号: {summary['buy_signals']}")
        print(f"卖出信号: {summary['sell_signals']}")
        
        if summary['first_signal_time']:
            print(f"首个信号时间: {summary['first_signal_time']}")
        if summary['last_signal_time']:
            print(f"最后信号时间: {summary['last_signal_time']}")
        print("="*40)


def run_simple_strategy(strategy: SimpleStrategyBase, data: pd.DataFrame, 
                       symbol: str = "BTC/USDT", initial_cash: float = 10000.0) -> List[Signal]:
    """
    运行简化策略的便捷函数
    
    Args:
        strategy: 策略实例
        data: K线数据
        symbol: 交易对
        initial_cash: 初始资金
        
    Returns:
        List[Signal]: 生成的信号列表
    """
    runner = SimpleStrategyRunner(strategy, initial_cash)
    return runner.run_strategy(data, symbol) 