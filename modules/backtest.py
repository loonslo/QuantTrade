import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from modules.position_manager import PositionManager, PyramidAllPositionManager


class Backtester:
    def __init__(self, strategy_func: Callable, position_manager: PositionManager = None):
        """
        初始化回测器
        :param strategy_func: 策略函数
        :param position_manager: 仓位管理器
        """
        self.strategy_func = strategy_func
        self.position_manager = position_manager or PyramidAllPositionManager()
        self.results = {}
        self.trades = []
        self.positions = []
        
    def run(self, df: pd.DataFrame, initial_capital: float = 10000, commission: float = 0.001):
        print("📊 开始回测...")
        signals = self.strategy_func(df)
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []
        equity_curve = []
        
        min_qty = 0.0001  # 虚拟币最小交易单位，可根据实际调整
        last_signal = 0  # 记录上一个信号，避免重复
        for i in range(1, len(df)):
            current_price = df['close'].iloc[i]
            current_signal = signals.iloc[i]
            
            # 信号去重：避免连续相同的信号
            if current_signal == last_signal:
                current_signal = 0
            last_signal = current_signal
            # 记录权益
            current_equity = capital + position * current_price
            equity_curve.append({
                'timestamp': df.index[i],
                'equity': current_equity,
                'price': current_price,
                'position': position,
                'signal': current_signal
            })
            # 买入逻辑（用position_manager）
            if current_signal == 1 and capital > 0:
                shares, cost = self.position_manager.on_buy_signal(capital, position, current_price, commission)
                if shares >= min_qty and cost <= capital:
                    position += shares
                    capital -= cost
                    entry_price = current_price
                    print(f"  >>> 买入成功: 数量={shares}, 价格={current_price}, 花费={cost}, 剩余资金={capital}")
                    trades.append({
                        'timestamp': df.index[i],
                        'action': 'BUY',
                        'price': current_price,
                        'shares': shares,
                        'cost': cost,
                        'capital': capital
                    })
                else:
                    print(f"  >>> 买入失败: 资金不足或低于最小交易单位({min_qty})")
                self.position_manager.reset() if current_signal == -1 else None
            # 卖出逻辑（用position_manager）
            elif current_signal == -1 and position > 0:
                sell_shares, revenue = self.position_manager.on_sell_signal(capital, position, current_price, commission)
                if sell_shares >= min_qty and sell_shares <= position:
                    capital += revenue
                    profit = revenue - (sell_shares * entry_price)
                    print(f"  >>> 卖出成功: 数量={sell_shares}, 价格={current_price}, 收入={revenue}, 盈亏={profit}, 剩余资金={capital}")
                    trades.append({
                        'timestamp': df.index[i],
                        'action': 'SELL',
                        'price': current_price,
                        'shares': sell_shares,
                        'revenue': revenue,
                        'profit': profit,
                        'capital': capital
                    })
                    position -= sell_shares
                    if position < 1e-8:
                        position = 0
                else:
                    print(f"  >>> 卖出失败: 持仓不足或低于最小交易单位({min_qty})")
                self.position_manager.reset() if current_signal == 1 else None
        self.results = {
            'initial_capital': initial_capital,
            'final_capital': capital + position * df['close'].iloc[-1],
            'total_return': (capital + position * df['close'].iloc[-1] - initial_capital) / initial_capital,
            'trades': trades,
            'equity_curve': equity_curve,
            'signals': signals
        }
        print("✅ 回测完成")
        
    def stats(self) -> Dict:
        """
        统计回测结果
        :return: 回测统计信息
        """
        if not self.results:
            return {}
        
        equity_curve = pd.DataFrame(self.results['equity_curve'])
        trades = self.results['trades']
        
        # 基础统计
        initial_capital = self.results['initial_capital']
        final_capital = self.results['final_capital']
        total_return = self.results['total_return']
        
        # 计算收益率序列
        equity_curve['returns'] = equity_curve['equity'].pct_change().fillna(0)
        
        # 年化收益率（假设数据是1分钟间隔）
        total_days = (equity_curve['timestamp'].iloc[-1] - equity_curve['timestamp'].iloc[0]).days
        if total_days > 0:
            annual_return = (1 + total_return) ** (365 / total_days) - 1
        else:
            annual_return = total_return
        
        # 夏普比率
        if equity_curve['returns'].std() > 0:
            sharpe_ratio = equity_curve['returns'].mean() / equity_curve['returns'].std() * np.sqrt(252 * 24 * 60)  # 年化
        else:
            sharpe_ratio = 0
        
        # 最大回撤
        equity_curve['cummax'] = equity_curve['equity'].cummax()
        equity_curve['drawdown'] = (equity_curve['equity'] - equity_curve['cummax']) / equity_curve['cummax']
        max_drawdown = equity_curve['drawdown'].min()
        
        # 交易统计
        # 统计所有买入和卖出相关的交易
        buy_trades = [t for t in trades if 'BUY' in t['action']]
        sell_trades = [t for t in trades if 'SELL' in t['action']]
        
        # 计算总手续费
        total_commission = 0
        for trade in trades:
            if 'cost' in trade:  # 买入交易
                commission_paid = trade['cost'] - (trade['shares'] * trade['price'])
                total_commission += commission_paid
            elif 'revenue' in trade:  # 卖出交易
                commission_paid = (trade['shares'] * trade['price']) - trade['revenue']
                total_commission += commission_paid
        
        win_trades = [t for t in sell_trades if t.get('profit', 0) > 0]
        loss_trades = [t for t in sell_trades if t.get('profit', 0) <= 0]
        
        win_rate = len(win_trades) / len(sell_trades) if sell_trades else 0
        avg_win = np.mean([t['profit'] for t in win_trades]) if win_trades else 0
        avg_loss = np.mean([t['profit'] for t in loss_trades]) if loss_trades else 0
        
        # 盈亏比
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        stats = {
            'initial_capital': initial_capital,
            'final_capital': final_capital,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'total_trades': len(sell_trades) + len(buy_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_days': total_days,
            'total_commission': total_commission,
            'commission_rate': total_commission / initial_capital if initial_capital > 0 else 0
        }
        
        return stats
    
    def print_summary(self):
        """打印回测摘要"""
        stats = self.stats()
        if not stats:
            print("❌ 没有回测结果")
            return
        
        print("\n📊 回测结果摘要")
        print("=" * 50)
        print(f"初始资金: ${stats['initial_capital']:,.2f}")
        print(f"最终资金: ${stats['final_capital']:,.2f}")
        print(f"总收益率: {stats['total_return']:.2%}")
        print(f"年化收益率: {stats['annual_return']:.2%}")
        print(f"夏普比率: {stats['sharpe_ratio']:.2f}")
        print(f"最大回撤: {stats['max_drawdown']:.2%}")
        print(f"总交易次数: {stats['total_trades']}")
        print(f"胜率: {stats['win_rate']:.2%}")
        print(f"平均盈利: ${stats['avg_win']:.2f}")
        print(f"平均亏损: ${stats['avg_loss']:.2f}")
        print(f"盈亏比: {stats['profit_factor']:.2f}")
        print(f"回测天数: {stats['total_days']}")
        print(f"总手续费: ${stats['total_commission']:.2f}")
        print(f"手续费率: {stats['commission_rate']:.2%}")
    
    def get_equity_curve(self) -> pd.DataFrame:
        """获取权益曲线"""
        if 'equity_curve' in self.results:
            return pd.DataFrame(self.results['equity_curve'])
        return pd.DataFrame()
    
    def get_trades(self) -> List[Dict]:
        """获取交易记录"""
        return self.results.get('trades', []) 