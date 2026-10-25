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


def build_equity_from_timereturn(
    time_returns: Dict[datetime, float],
    initial_cash: float,
    *,
    clip_min: float = -0.9,
    clip_max: float = 3.0,
    fillna_value: float = 0.0,
    smooth: bool = True,
    resample_rule: Optional[str] = None,
    interpolate: bool = False,
    interpolate_method: str = "linear",
) -> pd.DataFrame:
    """
    基于逐bar收益构建权益曲线，带缺失/异常值处理与可选平滑

    Returns:
        pd.DataFrame 索引为 datetime，列：['return', 'total_value']
    """
    if not time_returns:
        df = pd.DataFrame({"return": [], "total_value": []})
        return df

    ser = pd.Series(time_returns)
    ser.index = pd.to_datetime(ser.index)
    ser = ser.sort_index()

    # 处理异常/缺失
    ser = ser.replace([np.inf, -np.inf], np.nan)
    ser = ser.clip(lower=clip_min, upper=clip_max)
    ser = ser.fillna(fillna_value)

    # 可选重采样 + 插值：将稀疏时间序列对齐到固定频率
    if resample_rule:
        # 将收益视为离散时点的简单收益，缺失时视作0收益
        ser = ser.resample(resample_rule).asfreq()
        if interpolate:
            try:
                ser = ser.interpolate(method=interpolate_method, limit_direction="both")
            except Exception:
                ser = ser.fillna(0.0)
        else:
            ser = ser.fillna(0.0)

    # 可选平滑：简单移动平均（仅用于展示稳定性，不改变资金曲线总量级）
    if smooth and len(ser) >= 5:
        smoothed = ser.rolling(window=5, min_periods=1).mean()
    else:
        smoothed = ser

    equity = initial_cash * (1.0 + smoothed).cumprod()
    df = pd.DataFrame({"return": smoothed, "total_value": equity})
    return df

# --- 新增：权益曲线构建降级链入口 ---

def build_equity_with_fallbacks(
    *,
    time_returns: Optional[Dict[datetime, float]],
    price_series: Optional[pd.Series],
    std_trades: List[Dict[str, Any]],
    initial_cash: float,
    resample_rule: Optional[str] = None,
    interpolate: bool = True,
    interpolate_method: str = "linear",
    smooth: bool = True,
) -> pd.DataFrame:
    """
    优先基于 TimeReturn 构建；失败则使用 现金法(交易+价格) 构建；若仍失败则抛出异常由上层处理。
    返回列：['return', 'total_value']
    """
    # Level 1: TimeReturn
    if time_returns:
        try:
            return build_equity_from_timereturn(
                time_returns,
                initial_cash,
                clip_min=-0.9,
                clip_max=3.0,
                fillna_value=0.0,
                smooth=smooth,
                resample_rule=resample_rule,
                interpolate=interpolate,
                interpolate_method=interpolate_method,
            )
        except Exception:
            pass

    # Level 2: 现金法（需要价格与交易）
    if price_series is not None and len(price_series) > 0:
        equity_df = build_equity_cash_from_trades(price_series, std_trades, initial_cash)
        returns = equity_df["equity"].pct_change().replace([np.inf, -np.inf], 0.0).fillna(0.0)
        return pd.DataFrame({
            "return": returns,
            "total_value": equity_df["equity"],
        })

    # 其余情况交由调用方处理（例如仅起止点）
    raise RuntimeError("无法构建权益曲线：TimeReturn 与 现金法均不可用")


# --- 新增：从标准交易记录构建持仓与权益、现金序列 ---

def build_position_series_from_trades(
    std_trades: List[Dict[str, Any]],
    price_index: Iterable[pd.Timestamp],
) -> pd.Series:
    """
    根据标准交易记录累计得到持仓数量序列（按价格索引对齐，前向填充）
    """
    if not std_trades:
        return pd.Series(0.0, index=pd.DatetimeIndex(price_index), name="position")

    # 归一化交易：按时间排序
    def parse_dt_str(s: Any) -> pd.Timestamp:
        return pd.to_datetime(s)

    trades_df = pd.DataFrame(std_trades)
    trades_df["dt"] = trades_df["datetime"].apply(parse_dt_str)
    trades_df = trades_df.sort_values("dt")

    # 生成变更序列：买入 +qty，卖出 -qty
    trades_df["signed_qty"] = trades_df.apply(
        lambda r: float(r["quantity"]) if str(r["side"]).lower() == "buy" else -float(r["quantity"]), axis=1
    )
    qty_changes = trades_df.groupby("dt")["signed_qty"].sum()

    idx = pd.DatetimeIndex(price_index)
    qty_series = qty_changes.reindex(idx, method=None).fillna(0.0)
    position_series = qty_series.cumsum()
    position_series.name = "position"
    return position_series


def build_equity_cash_from_trades(
    price_series: pd.Series,
    std_trades: List[Dict[str, Any]],
    initial_cash: float,
) -> pd.DataFrame:
    """
    基于价格、标准交易与初始现金，按时间推进构建资金曲线（现金+持仓）
    返回列：['position', 'cash', 'equity']
    """
    idx = pd.DatetimeIndex(price_series.index).sort_values().unique()
    if not std_trades:
        # 无交易时，持仓=0，现金=初始资金，权益=现金
        return pd.DataFrame({
            "position": pd.Series(0.0, index=idx),
            "cash": pd.Series(float(initial_cash), index=idx),
            "equity": pd.Series(float(initial_cash), index=idx),
        })

    # 交易字典：按对齐到最近不晚于该时刻的bar聚合
    df_trades = pd.DataFrame(std_trades)
    df_trades["dt"] = pd.to_datetime(df_trades["datetime"])  # 使用 ISO 字符串
    df_trades = df_trades.sort_values("dt")

    aligned: Dict[Any, List[Dict[str, Any]]] = {}
    for _, row in df_trades.iterrows():
        t = pd.Timestamp(row["dt"])  # 实际交易时刻
        # 对齐至 idx 中不晚于 t 的最近索引（pad）。若不存在（t < 最早bar），则对齐到最早bar
        pos = idx.searchsorted(t, side="right") - 1
        if pos < 0:
            pos = 0
        ts_align = idx[pos]
        aligned.setdefault(ts_align, []).append(row.to_dict())

    position = 0.0
    cash = float(initial_cash)
    positions: List[float] = []
    cashes: List[float] = []
    equities: List[float] = []

    for ts, px in pd.Series(price_series.values, index=idx).items():
        # 处理该时刻所有交易（对齐后的）
        for tr in aligned.get(ts, []):
            side = str(tr.get("side", "buy")).lower()
            qty = float(tr.get("quantity", 0.0))
            price = float(tr.get("price", px))
            fee = float(tr.get("commission", 0.0))
            if side == "buy":
                cash -= qty * price
                cash -= fee
                position += qty
            else:
                cash += qty * price
                cash -= fee
                position -= qty
        equity = cash + position * float(px)
        positions.append(position)
        cashes.append(cash)
        equities.append(equity)

    return pd.DataFrame({
        "position": pd.Series(positions, index=idx),
        "cash": pd.Series(cashes, index=idx),
        "equity": pd.Series(equities, index=idx),
    })


# --- 新增：基于 FIFO 的逐笔卖出实现已实现盈亏计算 ---
