# coding=utf-8
"""
QuantTrade 配置包
整合安全配置和交易配置
"""

from config.secure import SecureConfig
from config.trading import TradingConfig

# 向后兼容
Config = SecureConfig

__all__ = ['SecureConfig', 'TradingConfig', 'Config']
