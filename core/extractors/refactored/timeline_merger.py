# -*- coding: utf-8 -*-
"""
量化交易系统 - 数据提取器模块（重构后）
========================================

重构说明:
- 原始文件: core/extractors.py (694行)
- 拆分后: 多个独立模块，平均每个 < 150行
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


def merge_strategy_timelines(
    strategy_to_series: Dict[str, Dict[str, pd.Series]]
) -> pd.DataFrame:
    """
    将多个策略的时间线（cash/position/equity 等）进行并表对齐

    Args:
        strategy_to_series: {strategy_name: {series_name: pd.Series}}

    Returns:
        pd.DataFrame: 多层列索引 DataFrame，(series_name, strategy_name)
    """
    if not strategy_to_series:
        return pd.DataFrame()

    frames: List[pd.DataFrame] = []
    for strat, series_map in strategy_to_series.items():
        df = pd.DataFrame(series_map)
        # 添加二级列：策略名
        df.columns = pd.MultiIndex.from_product([df.columns, [strat]])
        frames.append(df)

    merged = pd.concat(frames, axis=1).sort_index()
    return merged



