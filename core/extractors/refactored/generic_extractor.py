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
from .core_types import StandardTradeRecord

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Iterable, Union
from datetime import datetime, UTC

import numpy as np
import pandas as pd


def convert_generic_trades(
    trades: Union[List[Dict[str, Any]], List[tuple], pd.DataFrame],
    *,
    symbol_default: str,
    commission_rate: float = 0.0,
    strategy_name: Optional[str] = None,
    field_map: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    通用交易记录转换器：支持多种输入结构，输出标准化结构

    Args:
        trades: 支持 list[dict] / list[tuple] / pandas.DataFrame
        symbol_default: 默认交易对
        commission_rate: 手续费率（若输入未含手续费）
        strategy_name: 策略名称
        field_map: 可选字段映射，如 {'time': 'datetime', 'qty': 'quantity'}
    """
    std_records: List[Dict[str, Any]] = []
    if trades is None:
        return std_records

    def append_record(
        dt: Any,
        symbol: Any,
        side_val: Optional[str],
        qty: Any,
        price: Any,
        commission_val: Optional[float],
        trade_id: Optional[Any],
    ):
        try:
            dt_parsed = _parse_dt(dt)
            q = float(abs(float(qty)))
            p = float(price)
            # 过滤无效记录
            if not np.isfinite(q) or not np.isfinite(p) or q <= 0 or p <= 0:
                return
            side = _deduce_side(side_val, float(qty) if qty is not None else 0.0)
            fee = float(commission_val) if commission_val is not None else q * p * float(commission_rate or 0.0)
            # 生成订单ID（如果为空）
            if not trade_id or trade_id is None:
                trade_id = f"order_{dt_parsed.strftime('%Y%m%d_%H%M%S')}_{len(std_records)}"
            
            rec = StandardTradeRecord(
                id=str(trade_id),
                datetime=dt_parsed,
                symbol=str(symbol or symbol_default),
                side=side,
                quantity=q,
                price=p,
                commission=fee,
                pnl=0.0,  # 默认盈亏为0
                cash_before=100000.0,  # 默认现金
                cash_after=100000.0 - (q * p + fee),  # 简化计算
                position_before=0.0,  # 默认持仓
                position_after=q if side == "buy" else -q,  # 根据方向设置持仓
                strategy_name=strategy_name,
            )
            std_records.append(rec.to_dict())
        except Exception:
            # 跳过无法解析的记录
            return

    if isinstance(trades, pd.DataFrame):
        df = trades
        if df.empty:
            return std_records
        def map_col(name: str) -> Optional[str]:
            # 优先 field_map，其次常见别名
            if field_map and name in field_map and field_map[name] in df.columns:
                return field_map[name]
            aliases = {
                "datetime": ["datetime", "timestamp", "time", "dt"],
                "symbol": ["symbol", "asset", "code", "instrument"],
                "side": ["side", "action", "type"],
                "quantity": ["quantity", "qty", "size", "amount", "vol"],
                "price": ["price", "px", "rate"],
                "commission": ["commission", "fee", "fees"],
                "id": ["id", "order_id", "trade_id"],
            }
            for alias in aliases.get(name, []):
                if alias in df.columns:
                    return alias
            return None
        c_dt = map_col("datetime")
        c_sym = map_col("symbol")
        c_side = map_col("side")
        c_qty = map_col("quantity")
        c_px = map_col("price")
        c_fee = map_col("commission")
        c_id = map_col("id")
        # 必要字段：时间、数量、价格
        if c_dt is None or c_qty is None or c_px is None:
            return std_records
        for _, row in df.iterrows():
            append_record(
                dt=row[c_dt],
                symbol=(row[c_sym] if c_sym else symbol_default),
                side_val=(row[c_side] if c_side else None),
                qty=row[c_qty],
                price=row[c_px],
                commission_val=(row[c_fee] if c_fee else None),
                trade_id=(row[c_id] if c_id else None),
            )
        return std_records

    if isinstance(trades, list) and trades and isinstance(trades[0], dict):
        for d in trades:  # type: ignore[assignment]
            dd = {k.lower(): v for k, v in d.items()}
            get = lambda keys: next((dd[k] for k in keys if k in dd), None)
            dt = get(["datetime", "timestamp", "time", "dt"]) or datetime.now(UTC)
            sym = get(["symbol", "asset", "code", "instrument"]) or symbol_default
            side_val = get(["side", "action", "type"]) or None
            qty = get(["quantity", "qty", "size", "amount", "vol"]) or 0.0
            px = get(["price", "px", "rate"]) or 0.0
            fee = get(["commission", "fee", "fees"]) or None
            tid = get(["id", "order_id", "trade_id"]) or None
            append_record(dt, sym, side_val, qty, px, fee, tid)
        return std_records

    if isinstance(trades, list) and trades and not isinstance(trades[0], dict):
        # list of tuples: (dt, size/qty, price, [symbol], [side/id]) - 做宽松解析
        for tup in trades:  # type: ignore[assignment]
            try:
                # 确保类型转换正确
                dt_val = tup[0]
                dt = dt_val if isinstance(dt_val, (str, datetime)) else str(dt_val)

                qty_val = tup[1] if len(tup) > 1 else 0.0
                qty_or_size = float(qty_val) if qty_val is not None else 0.0

                price_val = tup[2] if len(tup) > 2 else 0.0
                price = float(price_val) if price_val is not None else 0.0

                sym_val = tup[3] if len(tup) > 3 else None
                sym = str(sym_val) if sym_val is not None else symbol_default

                extra = tup[4] if len(tup) > 4 else None
                side_val = None
                tid = None
                
                if isinstance(extra, str) and extra.lower() in ("buy", "sell", "b", "s", "long", "short"):
                    side_val = extra
                else:
                    tid = str(extra) if extra is not None else None
                
                append_record(dt, sym, side_val, qty_or_size, price, None, tid)
            except Exception:
                continue
        return std_records

    return std_records


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    try:
        # pandas Timestamp or str
        return pd.to_datetime(value).to_pydatetime()
    except Exception:
        raise ValueError(f"无法解析时间: {value}")


def _deduce_side(side_value: Optional[str], size_value: Optional[float]) -> str:
    if isinstance(side_value, str):
        s = side_value.lower()
        if s in ("buy", "sell"):
            return s
        if s in ("b", "long"):  # 宽松映射
            return "buy"
        if s in ("s", "short"):
            return "sell"
    if size_value is not None:
        return "buy" if size_value > 0 else "sell"
    return "buy"

