"""
回测引擎 - 基于 Backtrader 实现

实现 TradingEngine 接口，提供回测功能的交易引擎。
"""

from typing import Dict, Any, List, Optional
import backtrader as bt
import pandas as pd
import math

from .trading_engine import TradingEngine


class BacktestEngine(TradingEngine):
    """
    回测引擎
    
    基于 backtrader 实现的回测引擎，
    实现 TradingEngine 接口以便与 PortfolioManager 解耦。
    """
    
    def __init__(self, initial_cash: float = 100000.0, commission: float = 0.001):
        """
        初始化回测引擎
        
        Args:
            initial_cash: 初始资金
            commission: 手续费率
        """
        if not math.isfinite(initial_cash) or initial_cash <= 0 or not 0 <= commission < 1:
            raise ValueError('Initial cash must be positive and commission must be in [0, 1)')
        self.initial_cash = initial_cash
        self.commission = commission
        self._cash = initial_cash
        self._positions: Dict[str, Dict[str, Any]] = {}
        self._cerebro: Optional[bt.Cerebro] = None
        
    def buy(self, symbol: str, quantity: float, price: Optional[float] = None) -> Dict[str, Any]:
        """
        执行买入订单（回测）
        
        Args:
            symbol: 交易对
            quantity: 数量
            price: 价格
            
        Returns:
            Dict[str, Any]: 订单结果
        """
        if price is None:
            raise ValueError("回测引擎需要指定价格")
        if not all(math.isfinite(v) and v > 0 for v in (quantity, price)):
            raise ValueError('Quantity and price must be finite and positive')
        
        # 计算成本
        cost = quantity * price
        commission_fee = cost * self.commission
        total_cost = cost + commission_fee
        
        if total_cost > self._cash:
            return {
                'success': False,
                'error': f'现金不足: 需要 {total_cost:.2f}, 可用 {self._cash:.2f}',
                'symbol': symbol,
                'quantity': quantity,
                'price': price
            }
        
        # 扣除现金
        self._cash -= total_cost
        
        # 更新持仓
        if symbol in self._positions:
            old_pos = self._positions[symbol]
            old_qty = old_pos['quantity']
            old_price = old_pos['avg_price']
            new_qty = old_qty + quantity
            new_avg_price = (old_qty * old_price + cost) / new_qty
            self._positions[symbol] = {
                'quantity': new_qty,
                'avg_price': new_avg_price
            }
        else:
            self._positions[symbol] = {
                'quantity': quantity,
                'avg_price': price
            }
        
        return {
            'success': True,
            'symbol': symbol,
            'side': 'buy',
            'quantity': quantity,
            'price': price,
            'commission': commission_fee,
            'total_cost': total_cost,
            'cash_after': self._cash
        }
    
    def sell(self, symbol: str, quantity: float, price: Optional[float] = None) -> Dict[str, Any]:
        """
        执行卖出订单（回测）
        
        Args:
            symbol: 交易对
            quantity: 数量
            price: 价格
            
        Returns:
            Dict[str, Any]: 订单结果
        """
        if price is None:
            raise ValueError("回测引擎需要指定价格")
        if not all(math.isfinite(v) and v > 0 for v in (quantity, price)):
            raise ValueError('Quantity and price must be finite and positive')
        
        if symbol not in self._positions:
            return {
                'success': False,
                'error': f'无持仓: {symbol}',
                'symbol': symbol,
                'quantity': quantity,
                'price': price
            }
        
        pos = self._positions[symbol]
        if pos['quantity'] < quantity:
            return {
                'success': False,
                'error': f'持仓不足: 需要 {quantity}, 持有 {pos["quantity"]}',
                'symbol': symbol,
                'quantity': quantity,
                'available': pos['quantity']
            }
        
        # 计算收入
        revenue = quantity * price
        commission_fee = revenue * self.commission
        net_revenue = revenue - commission_fee
        
        # 增加现金
        self._cash += net_revenue
        
        # 计算已实现盈亏
        realized_pnl = (price - pos['avg_price']) * quantity
        
        # 更新持仓
        new_qty = pos['quantity'] - quantity
        if new_qty <= 0:
            del self._positions[symbol]
        else:
            self._positions[symbol] = {
                'quantity': new_qty,
                'avg_price': pos['avg_price']
            }
        
        return {
            'success': True,
            'symbol': symbol,
            'side': 'sell',
            'quantity': quantity,
            'price': price,
            'commission': commission_fee,
            'net_revenue': net_revenue,
            'realized_pnl': realized_pnl,
            'cash_after': self._cash
        }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        获取当前持仓
        
        Returns:
            List[Dict[str, Any]]: 持仓列表
        """
        return [
            {
                'symbol': symbol,
                'quantity': pos['quantity'],
                'avg_price': pos['avg_price']
            }
            for symbol, pos in self._positions.items()
        ]
    
    def get_balance(self) -> Dict[str, Any]:
        """
        获取账户余额
        
        Returns:
            Dict[str, Any]: 余额信息
        """
        return {
            'cash': self._cash,
            'total': self._cash + sum(
                pos['quantity'] * pos['avg_price'] 
                for pos in self._positions.values()
            )
        }
    
    def reset(self, initial_cash: Optional[float] = None):
        """
        重置引擎状态
        
        Args:
            initial_cash: 初始资金（可选）
        """
        if initial_cash is not None:
            if not math.isfinite(initial_cash) or initial_cash <= 0:
                raise ValueError('Initial cash must be finite and positive')
            self.initial_cash = initial_cash
        self._cash = self.initial_cash
        self._positions.clear()
