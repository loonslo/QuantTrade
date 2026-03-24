# coding=utf-8
"""
配置文件 [已迁移到 config 包]
向后兼容文件，请使用 config 包代替
"""
import warnings
warnings.warn("config.py 已迁移到 config/ 包，请使用 'from config import SecureConfig' 代替", DeprecationWarning)

from config.secure import SecureConfig

# 向后兼容
Config = SecureConfig
config = SecureConfig()

__all__ = ['SecureConfig', 'Config', 'config']
