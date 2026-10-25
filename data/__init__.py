"""
数据层模块
提供数据获取、存储和管理的功能，适配核心层接口
"""

from .providers.binance_provider import BinanceDataProvider
from .providers.csv_provider import CSVDataProvider
from .providers.database_provider import DatabaseDataProvider
from .storage.sqlite_storage import SQLiteStorage
from .storage.file_storage import FileStorage
# 移除数据缓存，直接使用数据库
from .validation.data_validator import DataValidator, data_validator

__all__ = [
    'BinanceDataProvider',
    'CSVDataProvider', 
    'DatabaseDataProvider',
    'SQLiteStorage',
    'FileStorage',
    'TradeRecordModel',
    # 'DataCache',  # 已移除
    # 'data_cache',  # 已移除
    'DataValidator',
    'data_validator'
] 