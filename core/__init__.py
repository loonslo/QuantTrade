"""
核心层模块
提供量化交易系统的核心功能，包括数据提供者、策略接口等
"""

from .data_provider import BaseDataProvider, MarketData
from .strategy_interface import Strategy, StrategyContext
from .position_interface import PositionManager, Position

__all__ = [
    'BaseDataProvider',
    'MarketData',
    'Strategy',
    'StrategyContext',
    'PositionManager',
    'Position'
] 