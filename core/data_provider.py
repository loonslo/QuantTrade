"""
数据提供者接口
定义数据获取的标准接口，支持多种数据源
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import pandas as pd
from dataclasses import dataclass
from utils.core.logger_manager import get_logger
from utils.validation.exceptions import DataException
from utils.time.timestamp_utils import TimestampConverter, Timestamp, normalize_timestamp

@dataclass
class MarketData:
    """标准市场数据结构，字段命名与主流交易所一致，timestamp为int（毫秒级Unix时间戳）"""
    symbol: str
    timestamp: int  # 毫秒级时间戳
    open: float
    high: float
    low: float
    close: float
    volume: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketData':
        # 统一处理时间戳，确保为毫秒级整数
        timestamp = normalize_timestamp(data['timestamp'])
        return cls(
            symbol=data['symbol'],
            timestamp=timestamp,
            open=float(data['open']),
            high=float(data['high']),
            low=float(data['low']),
            close=float(data['close']),
            volume=float(data['volume'])
        )
    
    def to_display_time(self) -> str:
        """转换为显示格式的时间字符串 (YYYY-mm-DD HH:MM:SS)"""
        return TimestampConverter.to_display_format(self.timestamp)
    
    def to_datetime(self) -> datetime:
        """转换为datetime对象"""
        return TimestampConverter.to_datetime(self.timestamp)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }

    def to_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp / 1000)

class BaseDataProvider(ABC):
    """数据提供者抽象基类，只定义核心接口，参数类型统一，包含参数校验和详细注释"""
    def __init__(self, name: str = "default"):
        self.name = name
        self.logger = get_logger('data_provider')

    @abstractmethod
    def get_ohlcv(self, symbol: str, timeframe: str, start_time: Optional[int] = None, end_time: Optional[int] = None, limit: Optional[int] = None) -> pd.DataFrame:
        """
        获取OHLCV数据
        Args:
            symbol: 交易对（如BTC/USDT）
            timeframe: 时间周期（如1m, 1h, 1d）
            start_time: 开始时间（毫秒级Unix时间戳）
            end_time: 结束时间（毫秒级Unix时间戳）
            limit: 数据条数限制
        Returns:
            pd.DataFrame: OHLCV数据，index为timestamp或datetime，columns为标准K线字段
        Raises:
            DataException: 数据获取失败时抛出
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现get_ohlcv方法")

    @abstractmethod
    def get_symbols(self) -> List[str]:
        """
        获取可用交易对列表
        Returns:
            List[str]: 交易对列表
        Raises:
            DataException: 获取失败时抛出
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现get_symbols方法")

    @abstractmethod
    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取市场信息
        Args:
            symbol: 交易对
        Returns:
            Dict[str, Any]: 市场信息
        Raises:
            DataException: 获取失败时抛出
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现get_market_info方法")

    def validate_symbol(self, symbol: str) -> bool:
        if not isinstance(symbol, str) or not symbol:
            self.logger.warning(f"validate_symbol: symbol参数无效: {symbol}")
            return False
        try:
            symbols = self.get_symbols()
            return symbol in symbols
        except Exception as e:
            self.logger.warning(f"验证交易对失败: {e}")
            return False

    def test_connection(self) -> bool:
        try:
            symbols = self.get_symbols()
            return len(symbols) > 0
        except Exception as e:
            self.logger.error(f"连接测试失败: {e}")
            return False

class DataProviderMixin:
    """
    通用便捷方法mixin，适用于所有BaseDataProvider子类。
    提供如获取最新价格、历史价格、数据摘要等常用功能。
    """
    def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取最新价格及24H涨跌幅
        Args:
            symbol: 交易对
        Returns:
            Optional[Dict[str, Any]]: {"price": float, "change_24h": float}
        Raises:
            DataException: 获取失败时抛出
        """
        try:
            df = self.get_ohlcv(symbol, '1m', limit=1)
            if not df.empty:
                price = float(df['close'].iloc[-1])
                change_24h = 0.0  # 无tick级别信息，默认0
                return {"price": price, "change_24h": change_24h}
            return None
        except Exception as e:
            self.logger.error(f"获取 {symbol} 最新价格失败: {e}")
            raise DataException(f"获取 {symbol} 最新价格失败: {e}", symbol, '1m')

    def get_price_history(self, symbol: str, timeframe: str, days: int = 30) -> pd.DataFrame:
        """
        获取指定天数的历史价格数据
        Args:
            symbol: 交易对
            timeframe: 时间周期
            days: 天数
        Returns:
            pd.DataFrame: 价格历史
        Raises:
            DataException: 获取失败时抛出
        """
        try:
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = end_time - days * 24 * 60 * 60 * 1000
            return self.get_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time
            )
        except Exception as e:
            self.logger.error(f"获取 {symbol} {timeframe} 历史价格失败: {e}")
            raise DataException(f"获取 {symbol} {timeframe} 历史价格失败: {e}", symbol, timeframe)

    def get_data_summary(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """
        获取数据摘要信息
        Args:
            symbol: 交易对
            timeframe: 时间周期
        Returns:
            Dict[str, Any]: 数据摘要
        Raises:
            DataException: 获取失败时抛出
        """
        try:
            df = self.get_ohlcv(symbol, timeframe, limit=1000)
            if df.empty:
                return {}
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'data_points': len(df),
                'start_time': df.index[0],
                'end_time': df.index[-1],
                'price_range': {
                    'min': float(df['low'].min()),
                    'max': float(df['high'].max()),
                    'current': float(df['close'].iloc[-1])
                },
                'volume_stats': {
                    'total': float(df['volume'].sum()),
                    'avg': float(df['volume'].mean()),
                    'max': float(df['volume'].max())
                }
            }
        except Exception as e:
            self.logger.error(f"获取 {symbol} {timeframe} 数据摘要失败: {e}")
            raise DataException(f"获取 {symbol} {timeframe} 数据摘要失败: {e}", symbol, timeframe) 