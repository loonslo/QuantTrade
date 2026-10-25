"""Shared Sys Backtrader execution for the API, CLI and research services."""

from __future__ import annotations

import math
from typing import Any

import backtrader as bt
import numpy as np
import pandas as pd

from analytics.performance import UnifiedPerformanceAnalyzer
from core.extractors.refactored import convert_backtrader_transactions
from strategies.registry import POSITION_CLASSES, STRATEGY_CLASSES
from utils.core.config_manager import BACKTEST_CONFIG, DEFAULT_SYMBOL


class EquityRecorder(bt.Analyzer):
    """Record broker equity on every bar, including indicator warm-up."""

    def start(self):
        self.rows = []

    def next(self):
        self.rows.append({
            "datetime": self.strategy.datetime.datetime().isoformat(),
            "total_value": self.strategy.broker.getvalue(),
            "cash": self.strategy.broker.getcash(),
            "position": self.strategy.position.size,
        })

    def get_analysis(self):
        return self.rows


def validate_market_data(data: pd.DataFrame) -> pd.DataFrame:
    """Validate a chronological UTC OHLCV snapshot without silently fixing it."""
    if len(data) < 2 or not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("At least two OHLCV bars with a DatetimeIndex are required")
    required = ["open", "high", "low", "close", "volume"]
    if missing := set(required) - set(data.columns):
        raise ValueError(f"Missing OHLCV columns: {sorted(missing)}")
    frame = data[required].astype(float).copy()
    if frame.index.hasnans or frame.index.has_duplicates or not frame.index.is_monotonic_increasing:
        raise ValueError("Bar timestamps must be valid, unique and increasing")
    if not np.isfinite(frame.to_numpy()).all():
        raise ValueError("OHLCV data must be finite")
    if (frame[["open", "high", "low", "close"]] <= 0).any().any() or (frame.volume < 0).any():
        raise ValueError("Prices must be positive and volume nonnegative")
    if ((frame.high < frame[["open", "close", "low"]].max(axis=1)) |
            (frame.low > frame[["open", "close", "high"]].min(axis=1))).any():
        raise ValueError("Invalid OHLC price range")
    frame.index = pd.to_datetime(frame.index, utc=True).tz_localize(None)
    return frame


def run_backtrader_backtest(
    *, strategy_name: str, position_type: str = "fixed_ratio", symbol: str | None = None,
    timeframe: str | None = None, start_cash: float | None = None,
    commission: float | None = None, slippage: float | None = None, limit: int = 500,
    data: pd.DataFrame | None = None, strategy_params: dict[str, Any] | None = None,
    position_params: dict[str, Any] | None = None, periods_per_year: float | None = None,
) -> dict[str, Any]:
    """Run a long-only spot backtest; market orders fill on the next bar.

    Supplying ``data`` keeps the whole operation offline. Without it, the existing
    Sys Binance provider is used explicitly. Results use fractional returns.
    """
    if strategy_name not in STRATEGY_CLASSES:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    if position_type not in POSITION_CLASSES:
        raise ValueError(f"Unknown position type: {position_type}")
    symbol = symbol or DEFAULT_SYMBOL
    timeframe = timeframe or BACKTEST_CONFIG["timeframe"]
    start_cash = float(BACKTEST_CONFIG["start_cash"] if start_cash is None else start_cash)
    commission = float(BACKTEST_CONFIG["commission"] if commission is None else commission)
    slippage = float(BACKTEST_CONFIG["slippage"] if slippage is None else slippage)
    if not all(math.isfinite(v) for v in (start_cash, commission, slippage)):
        raise ValueError("Cash, commission and slippage must be finite")
    if start_cash <= 0 or not 0 <= commission < 1 or not 0 <= slippage < 1:
        raise ValueError("Cash must be positive; commission and slippage must be in [0, 1)")
    if data is None:
        from data.providers.binance_provider import BinanceDataProvider
        data = BinanceDataProvider().get_ohlcv(symbol, timeframe, limit=limit)
    frame = validate_market_data(data)
    if periods_per_year is None:
        seconds = frame.index.to_series().diff().dropna().dt.total_seconds().median()
        periods_per_year = 365.25 * 86400 / seconds
    if not math.isfinite(periods_per_year) or periods_per_year <= 0:
        raise ValueError("periods_per_year must be finite and positive")

    cerebro = bt.Cerebro(stdstats=False)
    cerebro.adddata(bt.feeds.PandasData(dataname=frame), name=symbol)
    cerebro.broker.setcash(start_cash)
    cerebro.broker.setcommission(commission=commission)
    cerebro.broker.set_slippage_perc(slippage)
    cerebro.addstrategy(
        STRATEGY_CLASSES[strategy_name], **(strategy_params or {}),
        position_type=position_type, position_params=position_params or {},
    )
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trade")
    cerebro.addanalyzer(bt.analyzers.Transactions, _name="transactions")
    cerebro.addanalyzer(EquityRecorder, _name="equity")
    # Iterative mode handles datasets shorter than an indicator's warm-up period.
    strategy = cerebro.run(runonce=False)[0]
    final_equity = float(cerebro.broker.getvalue())
    curve = strategy.analyzers.equity.get_analysis()
    equity = pd.Series(
        [row["total_value"] for row in curve],
        index=pd.to_datetime([row["datetime"] for row in curve]), dtype=float,
    )
    returns = equity.pct_change().fillna(0.0)
    analyzer = UnifiedPerformanceAnalyzer(periods_per_year=periods_per_year)
    metrics = analyzer.calculate_all_metrics(returns)
    trades = convert_backtrader_transactions(
        strategy.analyzers.transactions.get_analysis(), commission_rate=commission,
        symbol_default=symbol, strategy_name=strategy_name, initial_cash=start_cash,
    )
    closed = strategy.analyzers.trade.get_analysis()
    total = int(closed.get("total", {}).get("closed", 0))
    won = closed.get("won", {})
    lost = closed.get("lost", {})
    gross_win = float(won.get("pnl", {}).get("total", 0))
    gross_loss = abs(float(lost.get("pnl", {}).get("total", 0)))
    return {
        "strategy_name": strategy_name, "position_type": position_type,
        "symbol": symbol, "timeframe": timeframe, "initial_cash": start_cash,
        "final_cash": final_equity, "final_equity": final_equity,
        "execution": "next_bar_open", "periods_per_year": periods_per_year,
        "performance": {
            "net_return": (final_equity - start_cash) / start_cash,
            "annual_return": metrics.annual_return, "sharpe_ratio": metrics.sharpe_ratio,
            "max_drawdown": abs(metrics.max_drawdown),
            "win_rate": int(won.get("total", 0)) / total if total else 0.0,
            "total_trades": total, "won_trades": int(won.get("total", 0)),
            "lost_trades": int(lost.get("total", 0)),
            "avg_win": float(won.get("pnl", {}).get("average", 0)),
            "avg_loss": float(lost.get("pnl", {}).get("average", 0)),
            "profit_factor": gross_win / gross_loss if gross_loss else None,
            "commission": commission, "slippage": slippage,
        },
        "trades": trades, "equity_curve": curve,
    }
