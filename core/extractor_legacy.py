"""
标准化数据提取与构建工具

- 交易记录标准化（Backtrader Transactions -> 标准结构）
- 权益曲线构建（基于逐bar收益），带缺失/异常值处理与可选平滑
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Iterable, Union
from datetime import datetime, UTC

import numpy as np
import pandas as pd


@dataclass
class StandardTradeRecord:
    id: Optional[str]
    datetime: datetime
    symbol: str
    side: str  # 'buy' | 'sell'
    quantity: float
    price: float
    commission: float
    pnl: Optional[float] = None
    cash_before: Optional[float] = None
    cash_after: Optional[float] = None
    position_before: Optional[float] = None
    position_after: Optional[float] = None
    strategy_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # 转换 datetime 为 ISO 字符串，便于 JSON 序列化
        data["datetime"] = self.datetime.isoformat() if isinstance(self.datetime, datetime) else str(self.datetime)
        return data


def convert_backtrader_transactions(
    transactions: Dict[datetime, List[list]],
    commission_rate: float,
    symbol_default: str,
    strategy_name: Optional[str] = None,
    initial_cash: float = 100000.0,
) -> List[Dict[str, Any]]:
    """
    将 Backtrader Transactions 分析器输出转换为标准交易记录

    transactions 结构示例：{ datetime: [ (data_name, size, price, sid) , ... ] }
    注意：BT 的 size>0 表示买入，size<0 表示卖出
    """
    std_records: List[Dict[str, Any]] = []
    if not transactions:
        return std_records
    
    # 持仓成本跟踪
    position_cost = 0.0
    position_size = 0.0
    # 现金状态跟踪
    current_cash = initial_cash

    for dt, tx_list in sorted(transactions.items(), key=lambda x: x[0]):
        for tx in tx_list or []:
            # 兼容不同 backtrader 版本的 tuple/list 长度
            # 尝试多种格式解析Backtrader交易记录
            data_name = symbol_default
            size = 0.0
            price = 0.0
            order_id = None
            
            try:
                # 分析Backtrader Transactions分析器的实际输出格式
                # 从日志看，格式可能是: [price, size, 0, order_id, amount]
                
                if len(tx) >= 5:
                    # 分析Backtrader Transactions分析器的实际输出格式
                    # 从日志看，格式可能是: [size, price, 0, order_id, amount]
                    potential_size = tx[0]
                    potential_price = tx[1]
                    
                    # 验证价格合理性（BTC价格通常在几万到十几万之间）
                    if isinstance(potential_price, (int, float)) and 10000 < potential_price < 200000:
                        # 格式正确：[size, price, 0, order_id, amount]
                        size = float(potential_size or 0.0)
                        price = float(potential_price)
                        print(f"✅ 成功解析：数量={size:.2f}, 价格={price:.2f}")
                    elif isinstance(potential_size, (int, float)) and 10000 < potential_size < 200000:
                        # 可能是 [price, size, 0, order_id, amount] 格式
                        price = float(potential_size)
                        size = float(potential_price or 0.0)
                        print(f"✅ 调整格式解析：价格={price:.2f}, 数量={size:.2f}")
                    else:
                        # 如果都不合理，尝试从成交金额计算
                        amount = tx[4]
                        if isinstance(amount, (int, float)) and abs(amount) > 0:
                            # 成交金额 = 价格 × 数量
                            if abs(potential_size) > 0:
                                calculated_price = abs(amount) / abs(potential_size)
                                if 10000 < calculated_price < 200000:
                                    price = calculated_price
                                    size = abs(potential_size)
                                    print(f"🔧 从成交金额计算：价格={price:.2f}, 数量={size:.2f}")
                
                # 如果上述方法都失败，使用原始逻辑作为后备
                if price <= 0:
                    if len(tx) >= 1 and tx[0] is not None:
                        data_name = tx[0]
                    if len(tx) >= 2:
                        size = float(tx[1] or 0.0)
                    if len(tx) >= 3:
                        price = float(tx[2] or 0.0)
                    if len(tx) >= 4:
                        order_id = str(tx[3]) if tx[3] is not None else None
                
                # 调试信息
                if price <= 0:
                    print(f"⚠️ 警告：无法获取有效价格，原始数据: {tx}")
                    print(f"   交易元组长度: {len(tx)}")
                    print(f"   尝试解析结果: size={size}, price={price}")
                    
            except Exception as e:
                print(f"❌ 交易记录解析失败: {e}, 原始数据: {tx}")
                # 容错：解析失败则跳过该条
                continue

            # 验证价格有效性
            if price <= 0:
                print(f"⚠️ 跳过无效价格的交易: 价格={price}, 数量={size}")
                continue

            side = "buy" if size > 0 else "sell"
            qty = abs(size)
            # 手续费计算：手续费率已经包含在交易数量中
            # 实际手续费 = 交易金额 × 手续费率
            commission = qty * price * float(commission_rate or 0.0)

            # 计算盈亏（基于持仓成本跟踪）
            pnl = 0.0
            if side == "buy":
                # 买入交易：更新持仓成本
                if position_size >= 0:  # 之前是空仓或持仓
                    # 计算新的平均持仓成本
                    total_cost = position_cost + (qty * price)
                    total_size = position_size + qty
                    if total_size > 0:
                        position_cost = total_cost
                        position_size = total_size
                else:  # 之前是空头，这是平空操作
                    # 平空盈利 = 空头成本 - 买入价格
                    pnl = abs(position_size) * (position_cost - price) - commission
                    position_cost = 0.0
                    position_size = 0.0
            elif side == "sell":
                # 卖出交易：计算盈亏
                if position_size > 0:  # 之前是持仓，这是平多操作
                    # 平多盈利 = 卖出价格 - 持仓成本
                    pnl = qty * (price - (position_cost / position_size)) - commission
                    # 更新持仓
                    position_size -= qty
                    if position_size <= 0:
                        position_cost = 0.0
                        position_size = 0.0
                else:  # 之前是空仓，这是开空操作
                    # 开空：记录空头成本
                    position_cost = price
                    position_size = -qty
            
            # 生成订单ID（如果为空）
            if not order_id or order_id == '':
                order_id = f"order_{dt.strftime('%Y%m%d_%H%M%S')}_{len(std_records)}"
            
            # 计算持仓状态
            position_before = position_size - (qty if side == "buy" else -qty)
            position_after = position_size
            
            # 计算现金状态（基于实际交易）
            cash_before = current_cash
            if side == "buy":
                # 买入：现金减少（下单金额，手续费已包含在数量中）
                # 实际买入数量 = qty，但现金减少 = qty * price（手续费已从数量中扣除）
                cash_after = current_cash - (qty * price)
                current_cash = cash_after
            else:  # sell
                # 卖出：现金增加（实际收到的金额，手续费已扣除）
                # 实际卖出数量 = qty，但现金增加 = qty * price（手续费已从数量中扣除）
                cash_after = current_cash + (qty * price)
                current_cash = cash_after
            
            record = StandardTradeRecord(
                id=order_id,
                datetime=dt,
                symbol=symbol_default,  # 使用默认交易对，而不是data_name
                side=side,
                quantity=qty,
                price=price,
                commission=commission,
                pnl=pnl,  # 添加盈亏字段
                cash_before=cash_before,
                cash_after=cash_after,
                position_before=position_before,
                position_after=position_after,
                strategy_name=strategy_name,
            )
            std_records.append(record.to_dict())

    return std_records


# --- 新增：通用交易记录适配器 ---

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


