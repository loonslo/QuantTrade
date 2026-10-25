"""
配置常量
定义项目中使用的所有常量值
"""

from typing import Final


class ConfigConstants:
    """配置常量类"""
    
    # 缓存配置
    CACHE_TIMEOUT: Final[int] = 3600  # 1小时
    CACHE_TIMEOUT_SHORT: Final[int] = 300  # 5分钟
    CACHE_TIMEOUT_LONG: Final[int] = 86400  # 24小时
    
    # 重试配置
    MAX_RETRIES: Final[int] = 3
    RETRY_DELAY: Final[float] = 1.0
    RETRY_BACKOFF_FACTOR: Final[float] = 2.0
    
    # 数据限制
    DEFAULT_LIMIT: Final[int] = 500
    MAX_LIMIT: Final[int] = 1000
    MIN_LIMIT: Final[int] = 1
    
    # 数值容差
    TOLERANCE: Final[float] = 1e-6
    PRICE_TOLERANCE: Final[float] = 1e-8
    
    # 时间间隔
    DEFAULT_TIMEFRAME: Final[str] = "1h"
    SUPPORTED_TIMEFRAMES: Final[tuple] = (
        '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h',
        '6h', '8h', '12h', '1d', '3d', '1w', '1M'
    )
    
    # 默认交易对
    DEFAULT_SYMBOL: Final[str] = "BTCUSDT"
    DEFAULT_QUOTE_ASSET: Final[str] = "USDT"
    
    # 数据库配置
    DB_CONNECTION_TIMEOUT: Final[int] = 30
    DB_QUERY_TIMEOUT: Final[int] = 60
    DB_POOL_SIZE: Final[int] = 10
    DB_MAX_OVERFLOW: Final[int] = 20
    
    # API配置
    API_TIMEOUT: Final[int] = 30
    API_RATE_LIMIT: Final[int] = 100  # 每分钟请求数
    API_RETRY_AFTER: Final[int] = 60  # 限流后等待时间
    
    # 技术指标参数
    RSI_PERIOD: Final[int] = 14
    MACD_FAST: Final[int] = 12
    MACD_SLOW: Final[int] = 26
    MACD_SIGNAL: Final[int] = 9
    BOLLINGER_PERIOD: Final[int] = 20
    BOLLINGER_STD: Final[float] = 2.0
    
    # 风险控制
    MAX_POSITION_SIZE: Final[float] = 0.1  # 最大仓位比例
    STOP_LOSS_PERCENT: Final[float] = 0.05  # 止损百分比
    TAKE_PROFIT_PERCENT: Final[float] = 0.1  # 止盈百分比
    
    # 日志配置
    LOG_LEVEL: Final[str] = "INFO"
    LOG_MAX_SIZE: Final[int] = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: Final[int] = 5
    
    # 文件路径
    CONFIG_FILE: Final[str] = "config.json"
    LOG_DIR: Final[str] = "logs"
    DATA_DIR: Final[str] = "data"
    CACHE_DIR: Final[str] = "cache"
    
    # 错误消息
    ERROR_MESSAGES: Final[dict] = {
        "INVALID_SYMBOL": "无效的交易对",
        "INVALID_TIMEFRAME": "无效的时间间隔",
        "DATA_NOT_FOUND": "未找到数据",
        "API_ERROR": "API调用失败",
        "DATABASE_ERROR": "数据库操作失败",
        "VALIDATION_ERROR": "数据验证失败"
    }
    
    # 成功消息
    SUCCESS_MESSAGES: Final[dict] = {
        "DATA_SAVED": "数据保存成功",
        "DATA_LOADED": "数据加载成功",
        "OPERATION_SUCCESS": "操作成功",
        "CONFIG_UPDATED": "配置更新成功"
    }
