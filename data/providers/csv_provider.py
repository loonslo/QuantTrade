"""
CSV数据提供者
提供从CSV文件读取数据的功能，适配核心层BaseDataProvider接口
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from pathlib import Path
from utils.core.logger_manager import get_logger
from utils.validation.exceptions import DataException
from core.data_provider import BaseDataProvider, DataProviderMixin


class CSVDataProvider(BaseDataProvider, DataProviderMixin):
    """CSV数据提供者"""
    
    def __init__(self, data_dir: str = "data_files/market_data"):
        """
        初始化CSV数据提供者
        
        Args:
            data_dir: 数据目录路径
        """
        super().__init__()
        self.logger = get_logger('csv_provider')
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def get_ohlcv(self, symbol: str, timeframe: str, start_time: Optional[int] = None, end_time: Optional[int] = None, limit: Optional[int] = None) -> pd.DataFrame:
        """
        从CSV文件获取OHLCV数据
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
            safe_symbol = symbol.replace('/', '_')
            filename = f"{safe_symbol}_{timeframe}.csv"
            filepath = self.data_dir / filename
            if not filepath.exists():
                self.logger.warning(f"CSV文件不存在: {filepath}")
                return pd.DataFrame()
            df = pd.read_csv(filepath)
            if 'timestamp' in df.columns:
                df['timestamp'] = df['timestamp'].astype(int)
                df.set_index('timestamp', inplace=True)
            # 时间过滤
            if start_time:
                df = df[df.index >= start_time]
            if end_time:
                df = df[df.index <= end_time]
            if limit and len(df) > limit:
                df = df.tail(limit)
            return df[['symbol', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            self.logger.error(f"从CSV加载 {symbol} 数据失败: {e}")
            raise DataException(f"从CSV加载 {symbol} 数据失败: {e}")

    def get_symbols(self) -> List[str]:
        """
        获取可用的交易对列表
        Returns:
            List[str]: 交易对列表
        Raises:
            DataException: 获取失败时抛出
        """
        try:
            symbols = []
            for file in self.data_dir.glob("*.csv"):
                filename = file.stem
                parts = filename.split('_')
                if len(parts) >= 2:
                    symbol_parts = parts[:-1]
                    symbol = '_'.join(symbol_parts).replace('_', '/')
                    symbols.append(symbol)
            return list(set(symbols))
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