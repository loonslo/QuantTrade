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


def attach_pnl_fifo(std_trades: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    为标准化交易记录附加已实现 PnL（仅对卖出记录计算并填写 'pnl'，买入保持为 None）。

    规则：
    - 使用 FIFO 成本法
    - 买入的手续费并入单位成本（price + fee/qty）
    - 卖出的手续费从卖出收入中扣减（整笔交易扣一次）
    - 若出现超卖（卖出数量大于持仓），超出部分视为即时卖空并以当根价格作为成本，
      对该超出部分不产生利润，仅扣除卖出手续费（保守处理，避免夸大利润）。
    """
    if not std_trades:
        return []

    # 复制并按时间排序（容忍字符串/时间对象）
    def _parse_dt(dt_val: Any) -> pd.Timestamp:
        try:
            return pd.to_datetime(dt_val)
        except Exception:
            return pd.Timestamp.utcnow()

    trades_sorted = sorted(std_trades, key=lambda t: _parse_dt(t.get("datetime")))

    # 库存：列表形式 [(remaining_qty: float, unit_cost: float)]，FIFO
    inventory: List[List[float]] = []
    enriched: List[Dict[str, Any]] = []

    for tr in trades_sorted:
        side = str(tr.get("side", "buy")).lower()
        qty = float(tr.get("quantity", 0.0) or 0.0)
        price = float(tr.get("price", 0.0) or 0.0)
        fee = float(tr.get("commission", 0.0) or 0.0)

        # 防御：过滤无效
        if not np.isfinite(qty) or not np.isfinite(price) or qty <= 0.0 or price <= 0.0:
            enriched.append({**tr})
            continue

        rec = {**tr}

        if side == "buy":
            # 买入：将手续费摊入单位成本
            unit_cost = price + (fee / qty if qty > 0 else 0.0)
            inventory.append([qty, unit_cost])
            # 买入不计算已实现 PnL
            rec["pnl"] = rec.get("pnl", None)
        else:
            # 卖出：以 FIFO 成本法实现收益
            remaining = qty
            realized = 0.0

            # 逐个耗用库存批次
            while remaining > 0 and inventory:
                lot = inventory[0]
                lot_qty, lot_cost = lot[0], lot[1]
                matched = lot_qty if lot_qty <= remaining else remaining
                realized += (price - lot_cost) * matched
                lot[0] -= matched
                remaining -= matched
                if lot[0] <= 0:
                    inventory.pop(0)

            # 对卖出手续费做扣减（整笔一次）
            realized -= fee

            # 若仍有未匹配的卖出数量（超卖），保守视为零利润（仅手续费影响已扣）
            # 因已扣整笔 fee，这里无需再次处理

            rec["pnl"] = realized

        enriched.append(rec)

    return enriched


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



