#!/usr/bin/env python3
"""
示例移动平均策略运行脚本
演示如何加载、配置和运行自定义策略
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional
import numpy as np

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from user_strategies.example_ma_strategy.strategy import ExampleMAStrategy
from core.strategy_interface import StrategyContext, Signal, Trade
from data.providers.binance_provider import BinanceDataProvider
from utils.logger import get_logger


class ExampleMAStrategyRunner:
    """示例移动平均策略运行器"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化策略运行器
        
        Args:
            config_path: 配置文件路径
        """
        self.logger = get_logger("example_ma_runner")
        self.config = self._load_config(config_path)
        self.strategy = None
        self.context = None
        self.data_provider = None
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.info(f"成功加载配置文件: {config_path}")
            return config
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            raise
    
    def initialize_data_provider(self) -> None:
        """初始化数据提供者"""
        try:
            backtest_config = self.config.get('backtest', {})
            symbols = backtest_config.get('symbols', ['BTC/USDT'])
            timeframe = backtest_config.get('timeframe', '1h')
            
            # 创建数据提供者
            self.data_provider = BinanceDataProvider()
            
            # 获取历史数据
            start_date = backtest_config.get('start_date', '2023-01-01')
            end_date = backtest_config.get('end_date', '2023-12-31')
            
            self.logger.info(f"获取历史数据: {symbols[0]} {start_date} 到 {end_date}")
            
            # 注意：当前使用模拟数据，未来将集成MCP真实数据提供者
            # 计划支持：
            # - 多种数据源: Binance, CoinGecko, Alpha Vantage
            # - 数据缓存和本地存储
            # - 实时数据流支持
            # 示例代码:
            # mcp_client = MCPClient()
            # self.data = mcp_client.get_historical_data(symbols[0], start_date, end_date)
            
            # 临时使用模拟数据（开发阶段）
            self._create_mock_data(symbols[0], start_date, end_date)
            
        except Exception as e:
            self.logger.error(f"初始化数据提供者失败: {e}")
            raise
    
    def _create_mock_data(self, symbol: str, start_date: str, end_date: str) -> None:
        """
        创建模拟数据用于演示
        
        注意：此方法将在MCP集成后替换为真实数据获取
        - 支持实时和历史数据
        - 数据质量验证
        - 缺失数据处理
        """
        try:
            # 创建时间序列
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            dates = pd.date_range(start=start, end=end, freq='1H')
            
            # 创建模拟价格数据
            np.random.seed(42)  # 确保可重复性
            base_price = 50000.0
            price_changes = np.random.normal(0, 0.02, len(dates))  # 2%标准差
            prices = [base_price]
            
            for change in price_changes[1:]:
                new_price = prices[-1] * (1 + change)
                prices.append(new_price)
            
            # 创建DataFrame
            self.data = pd.DataFrame({
                'datetime': dates,
                'open': prices,
                'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
                'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
                'close': prices,
                'volume': np.random.uniform(100, 1000, len(dates))
            })
            
            self.logger.info(f"创建模拟数据: {len(self.data)} 条记录")
            
        except Exception as e:
            self.logger.error(f"创建模拟数据失败: {e}")
            raise
    
    def initialize_strategy(self) -> None:
        """初始化策略"""
        try:
            # 获取策略参数
            strategy_params = self.config.get('parameters', {})
            
            # 创建策略实例
            self.strategy = ExampleMAStrategy(
                name=self.config.get('strategy_name', 'example_ma_strategy'),
                params=strategy_params
            )
            
            # 创建策略上下文
            initial_capital = self.config.get('backtest', {}).get('initial_capital', 10000.0)
            symbol = self.config.get('backtest', {}).get('symbols', ['BTC/USDT'])[0]
            
            self.context = StrategyContext(
                initial_cash=initial_capital,
                symbol=symbol
            )
            
            # 设置数据
            self.context.data = self.data
            
            # 初始化策略
            self.strategy.initialize(self.context)
            
            self.logger.info(f"策略初始化成功: {self.strategy.name}")
            
        except Exception as e:
            self.logger.error(f"初始化策略失败: {e}")
            raise
    
    def run_backtest(self) -> Dict[str, Any]:
        """运行回测"""
        try:
            self.logger.info("开始运行回测...")
            
            signals = []
            trades = []
            
            # 遍历每个K线数据
            for index, row in self.data.iterrows():
                # 更新当前时间
                self.context.current_time = row['datetime']
                
                # 准备K线数据
                bar_data = {
                    'datetime': row['datetime'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': row['volume']
                }
                
                # 添加技术指标（如果已计算）
                for col in self.data.columns:
                    if col.startswith(('sma_', 'ema_', 'rsi')):
                        bar_data[col] = row[col]
                
                # 生成信号
                signal = self.strategy.on_bar(self.context, pd.DataFrame([row]))
                
                if signal:
                    signals.append(signal)
                    self.logger.info(f"生成信号: {signal.signal_type} {signal.symbol} 价格: {signal.price:.2f}")
                    
                    # 模拟交易执行
                    trade = self._execute_trade(signal, row['close'])
                    if trade:
                        trades.append(trade)
                        self.strategy.on_trade(self.context, trade)
            
            # 计算回测结果
            results = self._calculate_backtest_results(signals, trades)
            
            self.logger.info("回测完成")
            return results
            
        except Exception as e:
            self.logger.error(f"运行回测失败: {e}")
            raise
    
    def _execute_trade(self, signal: Signal, current_price: float) -> Optional[Trade]:
        """模拟交易执行"""
        try:
            if signal.signal_type not in ['buy', 'sell']:
                return None
            
            # 计算交易数量
            position_size = self.strategy.params.get('position_size', 0.1)
            available_cash = self.context.current_cash
            
            if signal.signal_type == 'buy':
                # 买入逻辑
                trade_amount = available_cash * position_size
                quantity = trade_amount / current_price
                
                if quantity > 0:
                    # 更新现金
                    self.context.current_cash -= trade_amount
                    # 更新持仓
                    current_position = self.context.get_position(signal.symbol)
                    self.context.set_position(signal.symbol, current_position + quantity)
                    
                    return Trade(
                        id=f"trade_{len(self.context.trades) + 1}",
                        symbol=signal.symbol,
                        side='buy',
                        quantity=quantity,
                        price=current_price,
                        datetime=signal.datetime,
                        commission=trade_amount * 0.001  # 0.1%手续费
                    )
            
            elif signal.signal_type == 'sell':
                # 卖出逻辑
                current_position = self.context.get_position(signal.symbol)
                
                if current_position > 0:
                    # 计算卖出数量
                    sell_quantity = current_position * position_size
                    
                    if sell_quantity > 0:
                        # 更新现金
                        trade_amount = sell_quantity * current_price
                        self.context.current_cash += trade_amount
                        # 更新持仓
                        self.context.set_position(signal.symbol, current_position - sell_quantity)
                        
                        return Trade(
                            id=f"trade_{len(self.context.trades) + 1}",
                            symbol=signal.symbol,
                            side='sell',
                            quantity=sell_quantity,
                            price=current_price,
                            datetime=signal.datetime,
                            commission=trade_amount * 0.001  # 0.1%手续费
                        )
            
            return None
            
        except Exception as e:
            self.logger.error(f"执行交易失败: {e}")
            return None
    
    def _calculate_backtest_results(self, signals: list, trades: list) -> Dict[str, Any]:
        """计算回测结果"""
        try:
            # 计算总收益
            total_pnl = sum(trade.pnl or 0 for trade in trades)
            
            # 计算胜率
            win_trades = len([t for t in trades if t.pnl and t.pnl > 0])
            total_trades = len(trades)
            win_rate = win_trades / total_trades if total_trades > 0 else 0
            
            # 计算最大回撤
            equity_curve = []
            current_equity = self.context.initial_cash
            
            for trade in trades:
                current_equity += trade.pnl or 0
                equity_curve.append(current_equity)
            
            max_drawdown = 0
            peak = self.context.initial_cash
            
            for equity in equity_curve:
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            results = {
                'total_signals': len(signals),
                'total_trades': total_trades,
                'win_trades': win_trades,
                'loss_trades': total_trades - win_trades,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'max_drawdown': max_drawdown,
                'final_equity': current_equity,
                'return_rate': (current_equity - self.context.initial_cash) / self.context.initial_cash
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"计算回测结果失败: {e}")
            return {}
    
    def print_results(self, results: Dict[str, Any]) -> None:
        """打印回测结果"""
        try:
            print("\n" + "="*50)
            print("示例移动平均策略回测结果")
            print("="*50)
            print(f"总信号数: {results.get('total_signals', 0)}")
            print(f"总交易数: {results.get('total_trades', 0)}")
            print(f"盈利交易: {results.get('win_trades', 0)}")
            print(f"亏损交易: {results.get('loss_trades', 0)}")
            print(f"胜率: {results.get('win_rate', 0):.2%}")
            print(f"总盈亏: {results.get('total_pnl', 0):.2f}")
            print(f"最大回撤: {results.get('max_drawdown', 0):.2%}")
            print(f"最终资金: {results.get('final_equity', 0):.2f}")
            print(f"收益率: {results.get('return_rate', 0):.2%}")
            print("="*50)
            
        except Exception as e:
            self.logger.error(f"打印结果失败: {e}")
    
    def run(self) -> None:
        """运行完整的策略测试流程"""
        try:
            self.logger.info("开始运行示例移动平均策略")
            
            # 1. 初始化数据提供者
            self.initialize_data_provider()
            
            # 2. 初始化策略
            self.initialize_strategy()
            
            # 3. 运行回测
            results = self.run_backtest()
            
            # 4. 打印结果
            self.print_results(results)
            
            self.logger.info("策略运行完成")
            
        except Exception as e:
            self.logger.error(f"策略运行失败: {e}")
            raise


def main():
    """主函数"""
    try:
        # 创建策略运行器
        runner = ExampleMAStrategyRunner()
        
        # 运行策略
        runner.run()
        
    except Exception as e:
        print(f"运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 