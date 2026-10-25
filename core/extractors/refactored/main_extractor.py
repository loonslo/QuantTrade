# -*- coding: utf-8 -*-
"""
量化交易系统 - 数据提取器模块（主入口）
========================================

这是重构后的主入口文件，整合所有提取功能。

重构说明:
- 原始文件: core/extractors.py (694行)
- 拆分后: 8个功能模块，平均每个 < 120行
- 职责分离: 每个模块专注特定提取类型
- 易于维护: 修改不影响其他模块

作者：量化交易团队
版本：1.1.0
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Iterable, Union
from datetime import datetime, UTC

import numpy as np
import pandas as pd

# 导入所有核心类型
from .core_types import StandardTradeRecord

# 导入所有提取器
from .backtrader_extractor import convert_backtrader_transactions
from .generic_extractor import convert_generic_trades
from .equity_builder import build_equity_from_timereturn
from .equity_fallback import build_equity_with_fallbacks
from .position_builder import (
    build_position_series_from_trades,
    build_equity_cash_from_trades
)
from .pnl_calculator import attach_pnl_fifo
from .timeline_merger import merge_strategy_timelines

# 向后兼容：保持原有导入方式
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
