"""
数据库数据提供者
提供从数据库读取数据的功能，适配核心层BaseDataProvider接口
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from utils.core.logger_manager import get_logger
from utils.validation.exceptions import DataException
from core.data_provider import BaseDataProvider, DataProviderMixin
from ..storage.sqlite_storage import SQLiteStorage


class DatabaseDataProvider(BaseDataProvider, DataProviderMixin):
    """数据库数据提供者"""
    
    def __init__(self, db_path: str = "quant_trading.db"):
        """
        初始化数据库数据提供者
        
        Args:
            db_path: 数据库文件路径
        """
        super().__init__()
        self.logger = get_logger('database_provider')
        self.storage = SQLiteStorage(db_path)
    
    def get_ohlcv(self, symbol: str, timeframe: str, start_time: Optional[int] = None, end_time: Optional[int] = None, limit: Optional[int] = None) -> pd.DataFrame:
        """
        从数据库获取OHLCV数据
        Args:
            symbol: 交易对
            timeframe: 时间周期
            start_time: 开始时间（毫秒级Unix时间戳）
            end_time: 结束时间（毫秒级Unix时间戳）
            limit: 数据条数限制
        Returns:
            pd.DataFrame: OHLCV数据
        Raises:
            DataException: 获取失败时抛出
        """
        try:
            df = self.storage.load_market_data(symbol, start_time, end_time)
            if limit and len(df) > limit:
                df = df.tail(limit)
            if 'timestamp' in df.columns:
                df['timestamp'] = df['timestamp'].astype(int)
                df.set_index('timestamp', inplace=True)
            return df[['symbol', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            self.logger.error(f"从数据库加载 {symbol} 数据失败: {e}")
            raise DataException(f"从数据库加载 {symbol} 数据失败: {e}")

    def get_symbols(self) -> List[str]:
        """
        获取可用的交易对列表
        Returns:
            List[str]: 交易对列表
        Raises:
            DataException: 获取失败时抛出
        """
        try:
            summary = self.storage.get_data_summary()
            return list(summary.get('market_data', {}).keys())
        except Exception as e:
            self.logger.error(f"获取交易对列表失败: {e}")
            raise DataException(f"获取交易对列表失败: {e}")

    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取市场信息
        Args:
            symbol: 交易对
        Returns:
            Dict[str, Any]: 市场信息
        Raises:
            DataException: 获取失败时抛出
        """
        try:
            return {
                'symbol': symbol,
                'base_asset': symbol.split('/')[0] if '/' in symbol else 'UNKNOWN',
                'quote_asset': symbol.split('/')[1] if '/' in symbol else 'UNKNOWN',
                'min_qty': 0.001,
                'max_qty': 1000,
                'step_size': 0.001,
                'min_notional': 10,
                'precision': 6
            }
        except Exception as e:
            self.logger.error(f"获取市场信息失败: {e}")
            raise DataException(f"获取市场信息失败: {e}", symbol) 