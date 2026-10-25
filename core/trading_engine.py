"""
交易引擎抽象基类

定义回测和实盘交易的统一接口，确保回测引擎和实盘交易解耦。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class TradingEngine(ABC):
    """
    交易引擎抽象基类
    
    定义统一的交易接口，回测引擎和实盘交易都实现此接口，
    使得 PortfolioManager 不需要知道是回测还是实盘。
    """
    
    @abstractmethod
    def buy(self, symbol: str, quantity: float, price: Optional[float] = None) -> Dict[str, Any]:
        """
        执行买入订单
        
        Args:
            symbol: 交易对
            quantity: 数量
            price: 价格（None表示市价）
            
        Returns:
            Dict[str, Any]: 订单结果
        """
        pass
    
    @abstractmethod
    def sell(self, symbol: str, quantity: float, price: Optional[float] = None) -> Dict[str, Any]:
        """
        执行卖出订单
        
        Args:
            symbol: 交易对
            quantity: 数量
            price: 价格（None表示市价）
            
        Returns:
            Dict[str, Any]: 订单结果
        """
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        获取当前持仓
        
        Returns:
            List[Dict[str, Any]]: 持仓列表
        """
        pass
    
    @abstractmethod
    def get_balance(self) -> Dict[str, Any]:
        """
        获取账户余额
        
        Returns:
            Dict[str, Any]: 余额信息
        """
        pass
    
    @abstractmethod
    def reset(self, initial_cash: Optional[float] = None):
        """
        重置引擎状态
        
        Args:
            initial_cash: 初始资金（可选）
        """
        pass
