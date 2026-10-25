"""
增强策略运行器
提供更丰富的功能和更好的用户体验
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
from core.strategy_interface import StrategyContext, Signal
from strategies.base.simple_strategy_base import SimpleStrategyBase
from strategies.simple_strategy_runner import SimpleStrategyRunner
from utils.core.logger_manager import get_logger


class EnhancedStrategyRunner:
    """
    增强策略运行器
    提供更丰富的功能和更好的用户体验
    """
    
    def __init__(self, strategy: SimpleStrategyBase, initial_cash: float = 10000.0):
        """
        初始化增强策略运行器
        
        Args:
            strategy: 策略实例
            initial_cash: 初始资金
        """
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.logger = get_logger("enhanced_runner")
        
        # 运行状态
        self.signals: List[Signal] = []
        self.context = None
        self.performance_stats = {}
        
        # 创建基础运行器
        self.base_runner = SimpleStrategyRunner(strategy, initial_cash)
    
    def run_strategy(self, data: pd.DataFrame, symbol: str = "BTC/USDT", 
                    enable_analysis: bool = True) -> Dict[str, Any]:
        """
        运行策略并返回详细结果
        
        Args:
            data: K线数据 DataFrame
            symbol: 交易对
            enable_analysis: 是否启用性能分析
            
        Returns:
            Dict[str, Any]: 包含信号和性能统计的结果
        """
        try:
            self.logger.info(f"开始运行增强策略: {self.strategy.name}")
            
            # 运行基础策略
            signals = self.base_runner.run_strategy(data, symbol)
            self.signals = signals
            
            # 创建上下文
            self.context = StrategyContext(
                initial_cash=self.initial_cash,
                symbol=symbol
            )
            
            result = {
                'signals': signals,
                'strategy_name': self.strategy.name,
                'symbol': symbol,
                'data_length': len(data),
                'initial_cash': self.initial_cash
            }
            
            # 性能分析
            if enable_analysis and signals:
                result['performance'] = self._analyze_performance(data, signals)
            
            self.logger.info(f"策略运行完成，生成 {len(signals)} 个信号")
            return result
            
        except Exception as e:
            self.logger.error(f"策略运行失败: {e}")
            return {'signals': [], 'error': str(e)}
    
    def _analyze_performance(self, data: pd.DataFrame, signals: List[Signal]) -> Dict[str, Any]:
        """
        分析策略性能
        
        Args:
            data: K线数据
            signals: 信号列表
            
        Returns:
            Dict[str, Any]: 性能统计
        """
        try:
            # 基础统计
            buy_signals = [s for s in signals if s.signal_type == 'buy']
            sell_signals = [s for s in signals if s.signal_type == 'sell']
            
            # 信号时间分布
            signal_times = [s.datetime for s in signals if s.datetime]
            time_distribution = self._analyze_time_distribution(signal_times)
            
            # 信号强度分析
            strength_stats = self._analyze_signal_strength(signals)
            
            # 价格影响分析
            price_impact = self._analyze_price_impact(data, signals)
            
            return {
                'total_signals': len(signals),
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals),
                'buy_ratio': len(buy_signals) / len(signals) if signals else 0,
                'time_distribution': time_distribution,
                'strength_stats': strength_stats,
                'price_impact': price_impact,
                'first_signal': signals[0].datetime if signals else None,
                'last_signal': signals[-1].datetime if signals else None
            }
            
        except Exception as e:
            self.logger.error(f"性能分析失败: {e}")
            return {}
    
    def _analyze_time_distribution(self, signal_times: List[datetime]) -> Dict[str, Any]:
        """分析信号时间分布"""
        if not signal_times:
            return {}
        
        # 按小时分布
        hours = [t.hour for t in signal_times]
        hour_distribution = pd.Series(hours).value_counts().to_dict()
        
        # 按星期分布
        weekdays = [t.weekday() for t in signal_times]
        weekday_distribution = pd.Series(weekdays).value_counts().to_dict()
        
        return {
            'hour_distribution': hour_distribution,
            'weekday_distribution': weekday_distribution,
            'total_days': (max(signal_times) - min(signal_times)).days if len(signal_times) > 1 else 0
        }
    
    def _analyze_signal_strength(self, signals: List[Signal]) -> Dict[str, Any]:
        """分析信号强度"""
        if not signals:
            return {}
        
        strengths = [s.strength for s in signals]
        
        return {
            'mean_strength': np.mean(strengths),
            'std_strength': np.std(strengths),
            'min_strength': np.min(strengths),
            'max_strength': np.max(strengths),
            'strong_signals': len([s for s in signals if s.strength > 0.8]),
            'weak_signals': len([s for s in signals if s.strength < 0.5])
        }
    
    def _analyze_price_impact(self, data: pd.DataFrame, signals: List[Signal]) -> Dict[str, Any]:
        """分析价格影响"""
        if not signals or len(data) == 0:
            return {}
        
        try:
            # 计算信号前后的价格变化
            price_changes = []
            
            for signal in signals:
                if signal.datetime:
                    # 找到信号在数据中的位置
                    signal_idx = data[data['datetime'] == signal.datetime].index
                    if len(signal_idx) > 0:
                        idx = signal_idx[0]
                        if idx + 5 < len(data):  # 确保有后续数据
                            current_price = data.loc[idx, 'close']
                            future_price = data.loc[idx + 5, 'close']  # 5个周期后
                            change = (future_price - current_price) / current_price
                            price_changes.append(change)
            
            if price_changes:
                return {
                    'mean_price_change': np.mean(price_changes),
                    'std_price_change': np.std(price_changes),
                    'positive_changes': len([c for c in price_changes if c > 0]),
                    'negative_changes': len([c for c in price_changes if c < 0]),
                    'total_analyzed': len(price_changes)
                }
            
        except Exception as e:
            self.logger.error(f"价格影响分析失败: {e}")
        
        return {}
    
    def get_signal_summary(self) -> Dict[str, Any]:
        """获取信号摘要"""
        return self.base_runner.get_signal_summary()
    
    def print_detailed_summary(self) -> None:
        """打印详细摘要"""
        summary = self.get_signal_summary()
        
        if not summary:
            print("没有生成任何信号")
            return
        
        print("\n" + "="*50)
        print(f"策略: {self.strategy.name}")
        print("="*50)
        print(f"总信号数: {summary['total_signals']}")
        print(f"买入信号: {summary['buy_signals']}")
        print(f"卖出信号: {summary['sell_signals']}")
        
        if summary['first_signal_time']:
            print(f"首个信号时间: {summary['first_signal_time']}")
        if summary['last_signal_time']:
            print(f"最后信号时间: {summary['last_signal_time']}")
        
        # 显示性能统计
        if hasattr(self, 'performance_stats') and self.performance_stats:
            print("\n性能统计:")
            perf = self.performance_stats
            if 'strength_stats' in perf:
                strength = perf['strength_stats']
                print(f"  平均信号强度: {strength.get('mean_strength', 0):.3f}")
                print(f"  强信号数量: {strength.get('strong_signals', 0)}")
                print(f"  弱信号数量: {strength.get('weak_signals', 0)}")
            
            if 'price_impact' in perf:
                impact = perf['price_impact']
                if impact:
                    print(f"  平均价格变化: {impact.get('mean_price_change', 0):.3%}")
                    print(f"  正向变化: {impact.get('positive_changes', 0)}")
                    print(f"  负向变化: {impact.get('negative_changes', 0)}")
        
        print("="*50)


def run_enhanced_strategy(strategy: SimpleStrategyBase, data: pd.DataFrame, 
                         symbol: str = "BTC/USDT", initial_cash: float = 10000.0,
                         enable_analysis: bool = True) -> Dict[str, Any]:
    """
    运行增强策略的便捷函数
    
    Args:
        strategy: 策略实例
        data: K线数据
        symbol: 交易对
        initial_cash: 初始资金
        enable_analysis: 是否启用性能分析
        
    Returns:
        Dict[str, Any]: 包含信号和性能统计的结果
    """
    runner = EnhancedStrategyRunner(strategy, initial_cash)
    return runner.run_strategy(data, symbol, enable_analysis) 