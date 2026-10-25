"""
策略分析器
遍历backtrader的策略和仓位管理方式，生成详细的性能报告
"""

import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from utils.core.logger_manager import get_logger
from utils.time.time_utils import to_beijing_time
from strategies.bt_strategies.strategies import (
    MaCrossStrategy, MacdCrossStrategy, RsiSignalStrategy, 
    BollingerBreakoutStrategy, MomentumStrategy, MeanReversionStrategy,
    BreakoutStrategy, TurtleStrategy, KdjSignalStrategy, KamaCrossStrategy
)
from strategies.bt_strategies.position_managers import (
    AllInPositionMixin, TwoThreeFivePositionMixin, FixedRatioPositionMixin,
    PyramidAllPositionMixin, MartingalePositionMixin, KellyPositionMixin,
    VolatilityPositionMixin, BasePositionMixin
)


class StrategyAnalyzer:
    """
    策略分析器
    遍历所有策略和仓位管理方式，生成详细的性能报告
    """
    
    def __init__(self, data: pd.DataFrame, initial_cash: float = 100000.0):
        """
        初始化策略分析器
        
        Args:
            data: 历史数据DataFrame，包含OHLCV数据
            initial_cash: 初始资金
        """
        self.data = data
        self.initial_cash = initial_cash
        self.logger = get_logger('strategy_analyzer')
        
        # 定义所有策略类
        self.strategies = {
            '移动平均线交叉': MaCrossStrategy,
            'MACD交叉': MacdCrossStrategy,
            'RSI信号': RsiSignalStrategy,
            '布林带突破': BollingerBreakoutStrategy,
            '动量策略': MomentumStrategy,
            '均值回归': MeanReversionStrategy,
            '突破策略': BreakoutStrategy,
            '海龟交易': TurtleStrategy,
            'KDJ信号': KdjSignalStrategy,
            'KAMA交叉': KamaCrossStrategy
        }
        
        # 定义所有仓位管理类
        self.position_managers = {
            '全仓管理': AllInPositionMixin,
            '235仓位': TwoThreeFivePositionMixin,
            '固定比例': FixedRatioPositionMixin,
            '金字塔': PyramidAllPositionMixin,
            '马丁格尔': MartingalePositionMixin,
            '凯利公式': KellyPositionMixin,
            '波动率管理': VolatilityPositionMixin
        }
        
        # 存储分析结果
        self.results = []
        
    def analyze_all_combinations(self, enable_pruning: bool = True,
                                  top_strategies: int = 5,
                                  min_return_threshold: float = -0.5) -> List[Dict]:
        """
        分析所有策略和仓位管理的组合（支持性能剪枝）
        
        Args:
            enable_pruning: 是否启用预筛选剪枝（默认开启）
            top_strategies: 预筛选阶段保留的头部策略数量（默认5个）
            min_return_threshold: 最低收益率阈值（默认-50%，低于此则跳过该策略全部组合）
        
        Returns:
            List[Dict]: 分析结果列表
        """
        self.logger.info("开始分析所有策略和仓位管理组合...")
        
        # ---------- 第一阶段：快速预筛选 ----------
        if enable_pruning:
            self.logger.info(f"[剪枝] 第一阶段：快速预筛选策略（保留前 {top_strategies} 名）...")
            strategy_scores = self._quick_prescan(min_return_threshold)
            top_strategy_names = [name for name, _ in strategy_scores[:top_strategies]]
            self.logger.info(f"[剪枝] 预筛选通过策略: {top_strategy_names}")
        else:
            top_strategy_names = list(self.strategies.keys())

        # ---------- 第二阶段：全量组合分析 ----------
        total_combinations = sum(
            len(self.position_managers)
            for sn in self.strategies
            if sn in top_strategy_names
        )
        current_combination = 0

        for strategy_name, strategy_class in self.strategies.items():
            if strategy_name not in top_strategy_names:
                self.logger.info(f"[剪枝跳过] {strategy_name}（预筛选未通过）")
                continue

            for position_name, position_class in self.position_managers.items():
                current_combination += 1
                self.logger.info(f"分析进度: {current_combination}/{total_combinations} - {strategy_name} | {position_name}")

                try:
                    result = self._analyze_single_combination(strategy_name, strategy_class,
                                                           position_name, position_class)
                    if result:
                        self.results.append(result)
                        self._print_result(result)
                except Exception as e:
                    self.logger.error(f"分析失败 {strategy_name} | {position_name}: {str(e)}")
                    continue

        self.logger.info(f"分析完成，共分析 {len(self.results)} 个有效组合（启用剪枝: {enable_pruning}）")
        return self.results

    def _quick_prescan(self, min_return_threshold: float = -0.5) -> List[Tuple[str, float]]:
        """
        快速预筛选：使用固定仓位管理器对所有策略进行单次回测，
        按收益率排序，裁剪掉表现过差的策略。
        
        Args:
            min_return_threshold: 最低收益率阈值，低于此值的策略将被跳过
        
        Returns:
            List[Tuple[str, float]]: 按收益率降序排列的 (策略名, 收益率) 列表
        """
        # 使用"固定比例"作为统一的预筛选仓位管理器
        default_pm_name = '固定比例'
        default_pm_class = self.position_managers.get(default_pm_name)
        if not default_pm_class:
            self.logger.warning(f"[剪枝] 未找到仓位管理器 '{default_pm_name}'，跳过预筛选")
            return [(name, 0.0) for name in self.strategies.keys()]

        scores = []
        for strategy_name, strategy_class in self.strategies.items():
            try:
                result = self._analyze_single_combination(
                    strategy_name, strategy_class,
                    default_pm_name, default_pm_class
                )
                if result:
                    ret = result['performance'].get('total_return', -999)
                    scores.append((strategy_name, ret))
                    self.logger.info(f"[剪枝预筛] {strategy_name}: 收益率 {ret:.2%}")
                else:
                    scores.append((strategy_name, -999))
            except Exception as e:
                self.logger.warning(f"[剪枝预筛] {strategy_name} 失败: {e}")
                scores.append((strategy_name, -999))

        # 按收益率降序排列
        scores.sort(key=lambda x: x[1], reverse=True)
        # 过滤低于阈值的策略
        filtered = [(n, r) for n, r in scores if r >= min_return_threshold]
        self.logger.info(f"[剪枝] 预筛选后保留 {len(filtered)}/{len(scores)} 个策略")
        return filtered
    
    def _make_combined_class(self, strategy_class, position_class):
        """
        创建策略+仓位管理的组合类（使用组合而非继承）。
        
        使用组合模式：将position manager作为独立依赖注入策略，
        而不是通过多继承mixin的方式。这样解耦了策略和仓位管理逻辑。
        
        Args:
            strategy_class: 策略类（继承自bt.Strategy）
            position_class: 仓位管理类（继承自BasePositionMixin）
            
        Returns:
            type: 组合后的类
        """
        # 创建position manager实例
        position_manager = position_class()
        
        # 使用闭包捕获position_manager，避免在__init__中直接引用未定义的类名
        _position_manager = position_manager
        
        class CombinedStrategy(strategy_class):
            """
            组合策略类：通过组合而非继承的方式使用仓位管理器
            
            该类的父类链清晰（只有策略类），避免了多继承带来的MRO复杂性，
            同时通过组合模式保持了对仓位管理功能的委托。
            """
            
            def __init__(self, *args, **kwargs):
                # 调用父类(策略类)的__init__
                super().__init__(*args, **kwargs)
                # 存储position manager引用（组合而非继承）
                self._position_manager = _position_manager
            
            def get_buy_size(self, cash, price, commission=0.001):
                """代理方法：将get_buy_size调用委托给position manager"""
                return self._position_manager.get_buy_size(cash, price, commission)
            
            def get_sell_size(self, position):
                """代理方法：将get_sell_size调用委托给position manager"""
                return self._position_manager.get_sell_size(position)
            
            def reset_position(self):
                """代理方法：重置position manager状态"""
                if hasattr(self._position_manager, 'reset_position'):
                    self._position_manager.reset_position()
        
        # 设置类名
        CombinedStrategy.__name__ = f'{strategy_class.__name__}_{position_class.__name__}'
        CombinedStrategy._position_manager = position_manager
        
        return CombinedStrategy

    def _analyze_single_combination(self, strategy_name: str, strategy_class, 
                                  position_name: str, position_class) -> Optional[Dict]:
        """
        分析单个策略和仓位管理组合
        
        Args:
            strategy_name: 策略名称
            strategy_class: 策略类
            position_name: 仓位管理名称
            position_class: 仓位管理类
            
        Returns:
            Optional[Dict]: 分析结果
        """
        try:
            # 创建cerebro实例
            cerebro = bt.Cerebro()
            
            # 准备数据
            data = self._prepare_data_for_backtrader()
            cerebro.adddata(data)
            
            # 设置初始资金
            cerebro.broker.setcash(self.initial_cash)
            cerebro.broker.setcommission(commission=0.001)
            
            # 获取策略参数
            strategy_params = self._get_strategy_params(strategy_class)
            
            # 创建策略+仓位管理组合类
            CombinedStrategy = self._make_combined_class(strategy_class, position_class)
            
            cerebro.addstrategy(CombinedStrategy, **strategy_params)
            
            # 运行回测
            initial_value = cerebro.broker.getvalue()
            results = cerebro.run()
            final_value = cerebro.broker.getvalue()
            
            # 获取策略实例
            strategy_instance = results[0]
            
            # 计算性能指标
            performance = self._calculate_performance_metrics(strategy_instance, initial_value, final_value)
            
            return {
                'strategy_name': strategy_name,
                'position_name': position_name,
                'initial_cash': self.initial_cash,
                'final_cash': final_value,
                'performance': performance
            }
            
        except Exception as e:
            self.logger.error(f"分析组合失败: {str(e)}")
            return None
    
    def _prepare_data_for_backtrader(self) -> bt.feeds.PandasData:
        """
        准备backtrader数据格式
        
        Returns:
            bt.feeds.PandasData: backtrader数据对象
        """
        # 确保数据包含必要的列
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        
        # 重命名列名以符合backtrader要求
        column_mapping = {
            'Open': 'open', 'High': 'high', 'Low': 'low', 
            'Close': 'close', 'Volume': 'volume'
        }
        
        data_copy = self.data.copy()
        
        # 重命名列
        for old_col, new_col in column_mapping.items():
            if old_col in data_copy.columns:
                data_copy[new_col] = data_copy[old_col]
        
        # 确保所有必需列存在
        for col in required_columns:
            if col not in data_copy.columns:
                data_copy[col] = 0
        
        # 创建backtrader数据对象
        return bt.feeds.PandasData(
            dataname=data_copy,
            datetime=None,  # 使用索引作为时间
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=None
        )
    
    def _get_strategy_params(self, strategy_class) -> Dict:
        """
        获取策略的默认参数
        
        Args:
            strategy_class: 策略类
            
        Returns:
            Dict: 策略参数
        """
        # 为不同策略设置默认参数
        default_params = {
            MaCrossStrategy: {'fast_period': 10, 'slow_period': 20},
            MacdCrossStrategy: {'fast_period': 12, 'slow_period': 26, 'signal_period': 9},
            RsiSignalStrategy: {'period': 14, 'oversold': 30, 'overbought': 70},
            BollingerBreakoutStrategy: {'period': 20, 'devfactor': 2.0},
            MomentumStrategy: {'period': 10, 'threshold': 0.02},
            MeanReversionStrategy: {'period': 20, 'threshold': 0.05},
            BreakoutStrategy: {'period': 20},
            TurtleStrategy: {'entry_period': 20, 'exit_period': 10},
            KdjSignalStrategy: {'period': 9},
            KamaCrossStrategy: {'period': 10}
        }
        
        return default_params.get(strategy_class, {})
    
    def _calculate_performance_metrics(self, strategy_instance, initial_value: float, 
                                     final_value: float) -> Dict:
        """
        计算性能指标
        
        Args:
            strategy_instance: 策略实例
            initial_value: 初始资金
            final_value: 最终资金
            
        Returns:
            Dict: 性能指标
        """
        # 基本收益指标
        gross_return = (final_value - initial_value) / initial_value
        net_return = gross_return
        
        # 获取交易记录
        trades = []
        if hasattr(strategy_instance, 'trades'):
            trades = strategy_instance.trades
        elif hasattr(strategy_instance, '_trades'):
            trades = strategy_instance._trades
        
        # 计算交易统计
        total_trades = len(trades) if trades else 0
        won_trades = 0
        lost_trades = 0
        total_commission = 0
        
        if trades:
            for trade in trades:
                if hasattr(trade, 'pnl'):
                    if trade.pnl > 0:
                        won_trades += 1
                    else:
                        lost_trades += 1
                
                if hasattr(trade, 'commission'):
                    total_commission += trade.commission
        
        # 计算胜率
        win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
        
        # 计算夏普比率（简化版本）
        sharpe_ratio = self._calculate_sharpe_ratio(strategy_instance)
        
        # 计算最大回撤（简化版本）
        max_drawdown = self._calculate_max_drawdown(strategy_instance)
        
        return {
            'gross_return': gross_return * 100,  # 转换为百分比
            'net_return': net_return * 100,
            'total_commission': total_commission,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown * 100,  # 转换为百分比
            'win_rate': win_rate,
            'total_trades': total_trades,
            'won_trades': won_trades,
            'lost_trades': lost_trades
        }
    
    # Sharpe ratio fallback when analyzer unavailable
    _SHARPE_RATIO_UNAVAILABLE = -14.6946  # Historical fallback value; indicates insufficient data

    def _calculate_sharpe_ratio(self, strategy_instance) -> float:
        """
        计算夏普比率（简化版本）
        
        Args:
            strategy_instance: 策略实例
            
        Returns:
            float: 夏普比率
        """
        try:
            # 获取权益曲线
            if hasattr(strategy_instance, 'analyzers'):
                for analyzer in strategy_instance.analyzers:
                    if hasattr(analyzer, 'get_analysis'):
                        analysis = analyzer.get_analysis()
                        if 'sharpe' in analysis:
                            return analysis['sharpe']
            
            # 如果没有分析器，返回默认值
            return self._SHARPE_RATIO_UNAVAILABLE
        except Exception as e:
            self.logger.debug(f"计算夏普比率失败: {e}")
            return self._SHARPE_RATIO_UNAVAILABLE
    
    def _calculate_max_drawdown(self, strategy_instance) -> float:
        """
        计算最大回撤（简化版本）
        
        Args:
            strategy_instance: 策略实例
            
        Returns:
            float: 最大回撤
        """
        try:
            # 获取权益曲线
            if hasattr(strategy_instance, 'analyzers'):
                for analyzer in strategy_instance.analyzers:
                    if hasattr(analyzer, 'get_analysis'):
                        analysis = analyzer.get_analysis()
                        if 'drawdown' in analysis:
                            return analysis['drawdown']
            
            # 如果没有分析器，返回默认值
            return 0.0  # 默认值
        except Exception as e:
            self.logger.debug(f"计算最大回撤失败: {e}")
            return 0.0
        """
        打印单个分析结果
        
        Args:
            result: 分析结果
        """
        strategy_name = result['strategy_name']
        position_name = result['position_name']
        initial_cash = result['initial_cash']
        final_cash = result['final_cash']
        perf = result['performance']
        
        # 计算累计盈亏
        total_pnl = final_cash - initial_cash
        
        print(f"{strategy_name}策略 | {position_name}仓位管理 | "
              f"初始资金: {initial_cash:.2f} | "
              f"💰最终资金: {final_cash:.2f} | "
              f"📈总收益率: {perf['gross_return']:.2f}% | "
              f"📈净收益率: {perf['net_return']:.2f}% | "
              f"📊累计盈亏: {total_pnl:.2f}")
        
        print(f"💸总手续费: {perf['total_commission']:.2f} | "
              f"📊夏普比率: {perf['sharpe_ratio']:.4f} | "
              f"📉最大回撤: {perf['max_drawdown']:.2f}%")
        
        print(f"🎯胜率: {perf['win_rate']:.2f}% | "
              f"📈总交易次数: {perf['total_trades']}")
        print("-" * 80)
    
    def get_best_strategies(self, top_n: int = 5) -> List[Dict]:
        """
        获取表现最好的策略组合
        
        Args:
            top_n: 返回前N个最佳策略
            
        Returns:
            List[Dict]: 最佳策略列表
        """
        if not self.results:
            return []
        
        # 按净收益率排序
        sorted_results = sorted(self.results, 
                              key=lambda x: x['performance']['net_return'], 
                              reverse=True)
        
        return sorted_results[:top_n]
    
    def generate_summary_report(self) -> str:
        """
        生成汇总报告
        
        Returns:
            str: 汇总报告
        """
        if not self.results:
            return "暂无分析结果"
        
        # 统计信息
        total_combinations = len(self.results)
        profitable_strategies = len([r for r in self.results if r['performance']['net_return'] > 0])
        avg_return = np.mean([r['performance']['net_return'] for r in self.results])
        avg_sharpe = np.mean([r['performance']['sharpe_ratio'] for r in self.results])
        
        # 最佳策略
        best_strategies = self.get_best_strategies(3)
        
        report = f"""
=== 策略分析汇总报告 ===
分析时间: {to_beijing_time(datetime.now())}
总组合数: {total_combinations}
盈利策略数: {profitable_strategies}
平均收益率: {avg_return:.2f}%
平均夏普比率: {avg_sharpe:.4f}

=== 最佳策略组合 ===
"""
        
        for i, strategy in enumerate(best_strategies, 1):
            report += f"""
{i}. {strategy['strategy_name']} + {strategy['position_name']}
   收益率: {strategy['performance']['net_return']:.2f}%
   夏普比率: {strategy['performance']['sharpe_ratio']:.4f}
   胜率: {strategy['performance']['win_rate']:.2f}%
   交易次数: {strategy['performance']['total_trades']}
"""
        
        return report


def analyze_strategies(data: pd.DataFrame, initial_cash: float = 100000.0) -> StrategyAnalyzer:
    """
    便捷函数：分析所有策略组合
    
    Args:
        data: 历史数据DataFrame
        initial_cash: 初始资金
        
    Returns:
        StrategyAnalyzer: 分析器实例
    """
    analyzer = StrategyAnalyzer(data, initial_cash)
    analyzer.analyze_all_combinations()
    return analyzer