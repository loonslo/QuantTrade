"""
策略接口
定义策略的标准接口，支持多种策略类型
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd
from dataclasses import dataclass
from utils.core.logger_manager import get_logger


@dataclass
class Signal:
    """交易信号"""
    symbol: str
    signal_type: str  # 'buy', 'sell', 'hold'
    price: float
    datetime: datetime
    strength: float = 1.0  # 信号强度 0-1
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'symbol': self.symbol,
            'signal_type': self.signal_type,
            'price': self.price,
            'datetime': self.datetime,
            'strength': self.strength,
            'metadata': self.metadata or {}
        }


@dataclass
class Trade:
    """交易记录"""
    id: str
    symbol: str
    side: str  # 'buy', 'sell'
    quantity: float
    price: float
    datetime: datetime
    commission: float
    pnl: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'price': self.price,
            'datetime': self.datetime,
            'commission': self.commission,
            'pnl': self.pnl
        }


class StrategyContext:
    """策略上下文"""
    
    def __init__(self, initial_cash: float = 10000.0, symbol: Optional[str] = None):
        """
        初始化策略上下文
        
        Args:
            initial_cash: 初始资金
            symbol: 交易对
        """
        self.initial_cash = initial_cash
        self.current_cash = initial_cash
        self.positions: Dict[str, float] = {}  # symbol -> quantity
        self.trades: List[Trade] = []
        self.signals: List[Signal] = []
        self.current_time: Optional[datetime] = None
        self.data: Optional[pd.DataFrame] = None
        self.symbol: Optional[str] = symbol
    
    def get_position(self, symbol: str) -> float:
        """获取持仓数量"""
        return self.positions.get(symbol, 0.0)
    
    def set_position(self, symbol: str, quantity: float):
        """设置持仓数量"""
        self.positions[symbol] = quantity
    
    def add_trade(self, trade: Trade):
        """添加交易记录"""
        self.trades.append(trade)
    
    def add_signal(self, signal: Signal):
        """添加信号"""
        self.signals.append(signal)
    
    def get_total_value(self, current_prices: Dict[str, float]) -> float:
        """获取总资产价值"""
        total_value = self.current_cash
        
        for symbol, quantity in self.positions.items():
            if quantity != 0 and symbol in current_prices:
                total_value += quantity * current_prices[symbol]
        
        return total_value
    
    def get_portfolio_summary(self, current_prices: Dict[str, float]) -> Dict[str, Any]:
        """获取投资组合摘要"""
        total_value = self.get_total_value(current_prices)
        
        return {
            'initial_cash': self.initial_cash,
            'current_cash': self.current_cash,
            'total_value': total_value,
            'total_return': (total_value - self.initial_cash) / self.initial_cash,
            'positions': self.positions.copy(),
            'total_trades': len(self.trades),
            'total_signals': len(self.signals)
        }

    def get_symbol(self) -> Optional[str]:
        """获取当前交易对"""
        return self.symbol


class Strategy(ABC):
    """策略接口"""
    
    def __init__(self, name: str = "default"):
        """
        初始化策略
        
        Args:
            name: 策略名称
        """
        self.name = name
        self.logger = get_logger('strategy')
        self.context: Optional[StrategyContext] = None
    
    @abstractmethod
    def initialize(self, context: StrategyContext) -> None:
        """
        策略初始化
        
        Args:
            context: 策略上下文
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现initialize方法")
    
    @abstractmethod
    def on_bar(self, context: StrategyContext, data: pd.DataFrame) -> Optional[Signal]:
        """
        K线数据处理
        
        Args:
            context: 策略上下文
            data: K线数据
            
        Returns:
            Optional[Signal]: 交易信号，无信号时返回None
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现on_bar方法")
    
    @abstractmethod
    def on_trade(self, context: StrategyContext, trade: Trade) -> None:
        """
        交易事件处理
        
        Args:
            context: 策略上下文
            trade: 交易记录
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现on_trade方法")
    
    def on_signal(self, context: StrategyContext, signal: Signal) -> None:
        """
        信号事件处理
        
        Args:
            context: 策略上下文
            signal: 交易信号
        """
        context.add_signal(signal)
        # 移除重复的日志输出，统一在StrategyBase._display_signal_info中处理
    
    def calculate_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        计算技术指标
        
        Args:
            data: K线数据
            
        Returns:
            Dict[str, Any]: 技术指标
        """
        indicators = {}
        
        if len(data) < 2:
            return indicators
        
        # 计算移动平均线
        if len(data) >= 5:
            indicators['ma5'] = data['close'].rolling(window=5).mean().iloc[-1]
        if len(data) >= 10:
            indicators['ma10'] = data['close'].rolling(window=10).mean().iloc[-1]
        if len(data) >= 20:
            indicators['ma20'] = data['close'].rolling(window=20).mean().iloc[-1]
        
        # 计算RSI
        if len(data) >= 14:
            delta = data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = 100 - (100 / (1 + rs.iloc[-1]))
        
        # 计算布林带
        if len(data) >= 20:
            ma20 = data['close'].rolling(window=20).mean()
            std20 = data['close'].rolling(window=20).std()
            indicators['bb_upper'] = ma20.iloc[-1] + 2 * std20.iloc[-1]
            indicators['bb_middle'] = ma20.iloc[-1]
            indicators['bb_lower'] = ma20.iloc[-1] - 2 * std20.iloc[-1]
        
        return indicators
    
    def validate_signal(self, signal: Signal, context: StrategyContext) -> bool:
        """
        验证信号有效性
        
        Args:
            signal: 交易信号
            context: 策略上下文
            
        Returns:
            bool: 信号是否有效
        """
        if not signal or signal.signal_type not in ['buy', 'sell', 'hold']:
            return False
        
        if signal.price <= 0:
            return False
        
        if signal.strength < 0 or signal.strength > 1:
            return False
        
        return True
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        获取策略信息
        
        Returns:
            Dict[str, Any]: 策略信息
        """
        return {
            'name': self.name,
            'type': self.__class__.__name__,
            'description': getattr(self, 'description', ''),
            'parameters': getattr(self, 'parameters', {})
        }
    
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        设置策略参数
        
        Args:
            parameters: 参数字典
        """
        for key, value in parameters.items():
            if hasattr(self, key):
                setattr(self, key, value)
                self.logger.info(f"设置参数 {key} = {value}")
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        获取策略参数
        
        Returns:
            Dict[str, Any]: 参数字典
        """
        parameters = {}
        for attr in dir(self):
            if not attr.startswith('_') and not callable(getattr(self, attr)):
                value = getattr(self, attr)
                if isinstance(value, (int, float, str, bool)):
                    parameters[attr] = value
        return parameters 