"""
统一策略和仓位管理注册表
避免在多个文件中重复定义相同的映射关系
"""

from __future__ import annotations

from typing import Dict, Type

from strategies.bt_strategies.strategies_refactored import (
    MaCrossStrategy,
    MacdCrossStrategy,
    RsiSignalStrategy,
    BollingerBreakoutStrategy,
    MomentumStrategy,
    MeanReversionStrategy,
    BreakoutStrategy,
    TurtleStrategy,
    KdjSignalStrategy,
    KamaCrossStrategy,
)
from strategies.bt_strategies.position_managers import (
    AllInPositionMixin,
    TwoThreeFivePositionMixin,
    FixedRatioPositionMixin,
    PyramidAllPositionMixin,
    MartingalePositionMixin,
    KellyPositionMixin,
    VolatilityPositionMixin,
)

# 统一策略注册表
STRATEGY_CLASSES: Dict[str, Type] = {
    "ma_cross": MaCrossStrategy,
    "macd_cross": MacdCrossStrategy,
    "rsi_signal": RsiSignalStrategy,
    "bollinger_breakout": BollingerBreakoutStrategy,
    "momentum": MomentumStrategy,
    "mean_reversion": MeanReversionStrategy,
    "breakout": BreakoutStrategy,
    "turtle": TurtleStrategy,
    "kdj_signal": KdjSignalStrategy,
    "kama_cross": KamaCrossStrategy,
}

# 统一仓位管理注册表
POSITION_CLASSES: Dict[str, Type] = {
    "all_in": AllInPositionMixin,
    "235": TwoThreeFivePositionMixin,
    "two_three_five": TwoThreeFivePositionMixin,
    "fixed_ratio": FixedRatioPositionMixin,
    "pyramid": PyramidAllPositionMixin,
    "martingale": MartingalePositionMixin,
    "kelly": KellyPositionMixin,
    "volatility": VolatilityPositionMixin,
}


def get_strategy_class(strategy_name: str):
    """获取策略类"""
    return STRATEGY_CLASSES.get(strategy_name)


def get_position_class(position_type: str):
    """获取仓位管理类"""
    return POSITION_CLASSES.get(position_type) 
