"""
数据提取器模块（重构后）
整合所有提取功能
"""

from .core_types import StandardTradeRecord
from .backtrader_extractor import convert_backtrader_transactions
from .generic_extractor import convert_generic_trades
from .equity_builder import build_equity_from_timereturn
from .equity_fallback import build_equity_with_fallbacks
from .position_builder import build_position_series_from_trades, build_equity_cash_from_trades
from .pnl_calculator import attach_pnl_fifo
from .timeline_merger import merge_strategy_timelines

__all__ = [
    'StandardTradeRecord',
    'convert_backtrader_transactions',
    'convert_generic_trades',
    'build_equity_from_timereturn',
    'build_equity_with_fallbacks',
    'build_position_series_from_trades',
    'build_equity_cash_from_trades',
    'attach_pnl_fifo',
    'merge_strategy_timelines',
]
