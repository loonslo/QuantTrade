"""
简化策略基类
专注于核心交易逻辑，去除复杂的指标计算和状态管理
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
from utils.core.logger_manager import get_logger
from core.strategy_interface import Signal, StrategyContext


class SimpleStrategyBase(ABC):
    """
    简化策略基类
    专注于核心交易逻辑，最小化抽象层
    """
    
    def __init__(self, name: str = "simple_strategy", params: Optional[Dict[str, Any]] = None):
        """
        初始化简化策略基类
        
        Args:
            name: 策略名称
            params: 策略参数
        """
        self.name = name
        self.params = params or {}
        self.logger = get_logger(f'strategy.{name}')
    
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame, context: StrategyContext) -> Optional[Signal]:
        """
        生成交易信号（子类必须实现）
        
        Args:
            data: K线数据 DataFrame，包含 open, high, low, close, volume 等列
            context: 策略上下文
            
        Returns:
            Optional[Signal]: 交易信号，如果没有信号则返回None
            
        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现generate_signal方法")
    
    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """计算简单移动平均"""
        return data.rolling(window=period).mean()
    
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """计算指数移动平均"""
        return data.ewm(span=period).mean()
    
    def calculate_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def create_signal(self, symbol: str, signal_type: str, price: float, 
                     datetime: datetime, strength: float = 1.0) -> Signal:
        """
        创建交易信号
        
        Args:
            symbol: 交易对
            signal_type: 信号类型 ('buy', 'sell')
            price: 价格
            datetime: 时间
            strength: 信号强度 (0-1)
            
        Returns:
            Signal: 交易信号
        """
        return Signal(
            symbol=symbol,
            signal_type=signal_type,
            price=price,
            datetime=datetime,
            strength=strength
        )
    
    def log_signal(self, signal: Signal, data: pd.DataFrame) -> None:
        """记录信号日志"""
        current_price = data['close'].iloc[-1] if len(data) > 0 else 0
        self.logger.info(f"生成信号: {signal.signal_type} {signal.symbol} "
                        f"价格: {signal.price:.2f} 强度: {signal.strength:.2f}")
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证数据有效性"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_columns):
            self.logger.error(f"数据缺少必要列: {required_columns}")
            return False
        
        if len(data) == 0:
            self.logger.error("数据为空")
            return False
        
        return True 