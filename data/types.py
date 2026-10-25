"""
数据类型定义
定义项目中使用的所有数据结构类型
"""

from typing import TypedDict, List, Optional, Union
from datetime import datetime


class SymbolData(TypedDict):
    """币种数据"""
    symbol: str
    quote_asset: str
    price: float
    change_24h: float
    change_amount: float
    volume_24h: float
    market_cap: float
    rank: int
    updated_at: datetime
    source: str
    is_valid: bool


class MarketDataPoint(TypedDict):
    """市场数据点"""
    datetime: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class FearGreedData(TypedDict):
    """恐惧贪婪指数数据"""
    value: int
    classification: str
    classification_cn: str
    updated_at: datetime
    source: str
    is_valid: bool


class CoinDetailsData(TypedDict):
    """币种详情数据"""
    symbol: str
    price: float
    change_24h: float
    trend: str
    support: float
    resistance: float
    rsi: float
    macd_line: float
    macd_signal: float
    macd_histogram: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    volume_analysis: str
    volatility: float
    suggestion: str
    source: str
    updated_at: datetime


class MarketOverviewData(TypedDict):
    """市场概览数据"""
    btc: dict
    eth: dict
    market_sentiment: dict
    market_summary: dict
    last_updated: datetime


class ServiceResponse(TypedDict):
    """服务响应通用格式"""
    success: bool
    data: Union[List[dict], dict, None]
    count: int
    message: str


class DatabaseConfig(TypedDict):
    """数据库配置"""
    host: str
    port: int
    database: str
    username: str
    password: str


class CacheConfig(TypedDict):
    """缓存配置"""
    timeout: int
    max_retries: int
    retry_delay: float


class ApiConfig(TypedDict):
    """API配置"""
    base_url: str
    api_key: str
    timeout: int
    rate_limit: int
