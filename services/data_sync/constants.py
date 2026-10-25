# -*- coding: utf-8 -*-
"""
数据同步服务常量定义
统一管理默认交易对、时间框架等常量
"""

# 默认交易对列表
DEFAULT_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOTUSDT", 
    "SOLUSDT", "XRPUSDT", "DOGEUSDT"
]

# 支持的时间框架
SUPPORTED_TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']

# 时间框架限制配置 - 默认获取数据条数
# 注意: 这些是日常同步的默认条数，设置为100可以获取约3-4个月的历史数据
TIMEFRAME_LIMITS = {
    '1m': 100,     # 1分钟：100条 ≈ 约1.5天
    '5m': 100,     # 5分钟：100条 ≈ 约12天
    '15m': 100,    # 15分钟：100条 ≈ 约37天
    '1h': 100,     # 1小时：100条 ≈ 约4个月
    '4h': 100,     # 4小时：100条 ≈ 约16个月
    '1d': 100      # 1天：100条 ≈ 约3个月
}

# 手动同步时的最大限制
MAX_MANUAL_LIMITS = {
    '1m': 1000,   # 1分钟：最多1000条
    '5m': 1000,   # 5分钟：最多1000条
    '15m': 1000,  # 15分钟：最多1000条
    '1h': 1000,   # 1小时：最多1000条
    '4h': 1000,   # 4小时：最多1000条
    '1d': 1000    # 1天：最多1000条
}

# 需要合约指标的时间框架（持仓量和资金费率）
# 扩展为所有主要时间框架，确保各周期均写入 OI/资金费率
FUTURES_INDICATOR_TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d']

# 数据源标识
DATA_SOURCE_BINANCE = "binance"
DATA_SOURCE_COINGECKO = "coingecko"
DATA_SOURCE_ALTERNATIVE_ME = "alternative.me"
