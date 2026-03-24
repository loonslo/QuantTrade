#!/usr/bin/env python3
"""
交易配置文件 [已迁移到 config 包]
向后兼容文件，请使用 config 包代替
"""
import warnings
warnings.warn("trading_config.py 已迁移到 config/ 包，请使用 'from config import TradingConfig' 代替", DeprecationWarning)

from config.trading import TradingConfig

# 向后兼容
trading_config = TradingConfig()

__all__ = ['TradingConfig', 'trading_config']
