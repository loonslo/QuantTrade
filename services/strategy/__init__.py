# -*- coding: utf-8 -*-
"""
策略服务模块 - BACKEND
提供完整的策略管理和执行功能

主要功能：
- 策略管理
- 策略执行
- 回测服务
- 策略优化
- 风险控制
"""

from .strategy_service import StrategyService
from services.strategy.backtest_service import BacktestService

__all__ = [
"StrategyService",
"BacktestService"
]

__version__ = "2.0.0"
__author__ = "BACKEND Team"