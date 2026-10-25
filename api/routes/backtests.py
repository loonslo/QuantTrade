"""Offline research endpoints backed by the same engine as the command line."""

from datetime import datetime
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from core.backtrader_runner import run_backtrader_backtest
from strategies.registry import STRATEGY_CLASSES

router = APIRouter(prefix='/backtests', tags=['回测'])


class Bar(BaseModel):
    timestamp: datetime
    open: float = Field(gt=0, allow_inf_nan=False)
    high: float = Field(gt=0, allow_inf_nan=False)
    low: float = Field(gt=0, allow_inf_nan=False)
    close: float = Field(gt=0, allow_inf_nan=False)
    volume: float = Field(ge=0, allow_inf_nan=False)


class BacktestRequest(BaseModel):
    strategy_name: str = 'ma_cross'
    symbol: str = 'BTC/USDT'
    timeframe: str = '1h'
    position_type: str = 'fixed_ratio'
    initial_cash: float = Field(default=10000, gt=0, allow_inf_nan=False)
    commission: float = Field(default=0.001, ge=0, lt=1, allow_inf_nan=False)
    slippage: float = Field(default=0, ge=0, lt=1, allow_inf_nan=False)
    strategy_params: dict[str, Any] = Field(default_factory=dict)
    position_params: dict[str, Any] = Field(default_factory=dict)
    periods_per_year: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    bars: list[Bar] = Field(min_length=2, max_length=100000)


@router.get('/strategies')
def strategies():
    return {'success': True, 'data': sorted(STRATEGY_CLASSES)}


@router.post('')
async def backtest(request: BacktestRequest):
    frame = pd.DataFrame([bar.model_dump() for bar in request.bars]).set_index('timestamp')
    try:
        result = await run_in_threadpool(
            run_backtrader_backtest, strategy_name=request.strategy_name,
            position_type=request.position_type, symbol=request.symbol,
            timeframe=request.timeframe, start_cash=request.initial_cash,
            commission=request.commission, slippage=request.slippage, data=frame,
            strategy_params=request.strategy_params, position_params=request.position_params,
            periods_per_year=request.periods_per_year,
        )
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {'success': True, 'data': result}
