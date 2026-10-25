"""
多策略组合回测引擎
支持多标的同时持仓与现金约束，实现真正的投资组合管理
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
from utils.core.logger_manager import get_logger
from .portfolio_manager import PortfolioManager, TradingConstraints
from data.providers.binance_provider import BinanceDataProvider
from analytics.performance import UnifiedPerformanceAnalyzer


class PortfolioBacktestEngine:
    """多策略组合回测引擎"""
    
    def __init__(self, initial_cash: float = 100000.0):
        """
        初始化组合回测引擎
        
        Args:
            initial_cash: 初始现金
        """
        self.logger = get_logger('portfolio_backtest_engine')
        self.portfolio_manager = PortfolioManager(initial_cash)
        self.performance_analyzer = UnifiedPerformanceAnalyzer()
        self.data_provider = BinanceDataProvider()
        
        # 回测状态
        self.current_prices: Dict[str, float] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []
        
        self.logger.info(f"🚀 组合回测引擎初始化完成，初始现金: {initial_cash:,.2f}")
    
    def add_trading_constraints(self, symbol: str, constraints: TradingConstraints):
        """
        添加交易约束
        
        Args:
            symbol: 交易对
            constraints: 交易约束
        """
        self.portfolio_manager.add_trading_constraints(symbol, constraints)
    
    def update_prices(self, prices: Dict[str, float]):
        """
        更新当前价格
        
        Args:
            prices: 价格字典 {symbol: price}
        """
        self.current_prices.update(prices)
        
        # 更新权益曲线
        self._update_equity_curve()
    
    def execute_buy_order(self, symbol: str, quantity: float, price: float,
                         commission_rate: float = 0.001, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        执行买入订单
        
        Args:
            symbol: 交易对
            quantity: 数量
            price: 价格
            commission_rate: 手续费率
            timestamp: 时间戳
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 执行订单
            result = self.portfolio_manager.execute_buy_order(
                symbol, quantity, price, commission_rate, timestamp
            )
            
            # 记录交易历史
            self.trade_history.append(result)
            
            # 更新当前价格
            self.current_prices[symbol] = price
            
            # 更新权益曲线
            self._update_equity_curve()
            
            # 验证一致性
            self._validate_consistency()
            
            return result
            
        except Exception as e:
            self.logger.error(f"买入订单执行失败: {e}")
            raise
    
    def execute_sell_order(self, symbol: str, quantity: float, price: float,
                          commission_rate: float = 0.001, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        执行卖出订单
        
        Args:
            symbol: 交易对
            quantity: 数量
            price: 价格
            commission_rate: 手续费率
            timestamp: 时间戳
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        try:
            # 执行订单
            result = self.portfolio_manager.execute_sell_order(
                symbol, quantity, price, commission_rate, timestamp
            )
            
            # 记录交易历史
            result['side'] = 'sell'  # 确保side字段正确
            self.trade_history.append(result)
            
            # 更新当前价格
            self.current_prices[symbol] = price
            
            # 更新权益曲线
            self._update_equity_curve()
            
            # 验证一致性
            self._validate_consistency()
            
            return result
            
        except Exception as e:
            self.logger.error(f"卖出订单执行失败: {e}")
            raise
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        获取投资组合摘要
        
        Returns:
            Dict[str, Any]: 投资组合摘要
        """
        return self.portfolio_manager.get_portfolio_summary(self.current_prices)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标
        
        Returns:
            Dict[str, Any]: 性能指标
        """
        try:
            # 构建权益曲线DataFrame
            equity_df = pd.DataFrame()
            if self.equity_curve:
                equity_df = pd.DataFrame(self.equity_curve)
                if 'timestamp' in equity_df.columns and 'total_value' in equity_df.columns:
                    equity_df['timestamp'] = pd.to_datetime(equity_df['timestamp'])
                    equity_df = equity_df.set_index('timestamp')['total_value'].sort_index()
            
            # 计算性能指标
            metrics = self.performance_analyzer.calculate_metrics(
                trades=self.trade_history,
                equity_curve=equity_df,
                initial_cash=self.portfolio_manager.initial_cash,
                final_cash=self.portfolio_manager.get_total_value(self.current_prices)
            )
            
            return {
                'total_return': metrics.total_return,
                'annualized_return': metrics.annualized_return,
                'sharpe_ratio': metrics.sharpe_ratio,
                'max_drawdown': metrics.max_drawdown,
                'win_rate': metrics.win_rate,
                'total_trades': metrics.total_trades,
                'profit_factor': metrics.profit_factor
            }
            
        except Exception as e:
            self.logger.warning(f"性能指标计算失败: {e}")
            return {}
    
    def _update_equity_curve(self):
        """更新权益曲线"""
        try:
            total_value = self.portfolio_manager.get_total_value(self.current_prices)
            
            equity_point = {
                'timestamp': datetime.now().isoformat(),
                'total_value': total_value,
                'cash': self.portfolio_manager.get_cash(),
                'positions_value': total_value - self.portfolio_manager.get_cash()
            }
            
            self.equity_curve.append(equity_point)
            
        except Exception as e:
            self.logger.warning(f"权益曲线更新失败: {e}")
    
    def _validate_consistency(self):
        """验证一致性"""
        try:
            is_consistent, errors = self.portfolio_manager.validate_consistency(self.current_prices)
            if not is_consistent:
                self.logger.warning(f"投资组合一致性检查失败: {errors}")
        except Exception as e:
            self.logger.warning(f"一致性检查失败: {e}")
    
    def run_backtest(self, strategy_signals: List[Dict[str, Any]], 
                    price_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        运行组合回测
        
        Args:
            strategy_signals: 策略信号列表
            price_data: 价格数据 {symbol: DataFrame}
            
        Returns:
            Dict[str, Any]: 回测结果
        """
        self.logger.info("🚀 开始组合回测...")
        
        try:
            # 按时间排序信号
            sorted_signals = sorted(strategy_signals, key=lambda x: x.get('timestamp', ''))
            
            for signal in sorted_signals:
                symbol = signal.get('symbol')
                action = signal.get('action')  # 'buy' or 'sell'
                quantity = signal.get('quantity', 0)
                price = signal.get('price', 0)
                timestamp = signal.get('timestamp')
                
                if not all([symbol, action, quantity, price]):
                    self.logger.warning(f"跳过无效信号: {signal}")
                    continue
                
                # 更新价格
                self.update_prices({symbol: price})
                
                # 执行交易
                if action == 'buy' and quantity > 0:
                    self.execute_buy_order(symbol, quantity, price, timestamp=timestamp)
                elif action == 'sell' and quantity > 0:
                    self.execute_sell_order(symbol, quantity, price, timestamp=timestamp)
            
            # 获取最终结果
            portfolio_summary = self.get_portfolio_summary()
            performance_metrics = self.get_performance_metrics()
            
            result = {
                'portfolio_summary': portfolio_summary,
                'performance_metrics': performance_metrics,
                'trade_history': self.trade_history,
                'equity_curve': self.equity_curve,
                'final_prices': self.current_prices
            }
            
            self.logger.info("✅ 组合回测完成")
            return result
            
        except Exception as e:
            self.logger.error(f"组合回测失败: {e}")
            raise
    
    def reset(self, new_cash: Optional[float] = None):
        """重置回测引擎"""
        self.portfolio_manager.reset(new_cash)
        self.current_prices.clear()
        self.trade_history.clear()
        self.equity_curve.clear()
        self.logger.info("🔄 组合回测引擎已重置")
    
    def get_consistency_report(self) -> Dict[str, Any]:
        """
        获取一致性报告
        
        Returns:
            Dict[str, Any]: 一致性报告
        """
        try:
            is_consistent, errors = self.portfolio_manager.validate_consistency(self.current_prices)
            
            # 计算理论总价值
            calculated_total = self.portfolio_manager.get_total_value(self.current_prices)
            actual_total = self.portfolio_manager.cash + sum(
                pos.quantity * self.current_prices.get(symbol, pos.avg_price)
                for symbol, pos in self.portfolio_manager.positions.items()
            )
            
            return {
                'is_consistent': is_consistent,
                'errors': errors,
                'calculated_total': calculated_total,
                'actual_total': actual_total,
                'difference': abs(calculated_total - actual_total),
                'cash': self.portfolio_manager.cash,
                'positions_count': len(self.portfolio_manager.positions),
                'total_trades': len(self.trade_history)
            }
            
        except Exception as e:
            self.logger.error(f"一致性报告生成失败: {e}")
            return {'error': str(e)} 