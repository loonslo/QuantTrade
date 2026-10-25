"""
量化交易系统 - 交易策略模块（已重构）
========================================

本模块已被重构，现在使用独立的策略文件。

主要变更：
- BaseCryptoStrategy基类移至 base_strategy.py
- 仓位管理工具移至 position_utils.py
- 每个策略独立文件存储在 individual/ 目录下

目录结构：
├── strategies.py           # 本文件：聚合导入
├── base_strategy.py        # 策略基类
├── position_utils.py       # 仓位管理工具
├── position_managers.py    # 仓位管理实现
└── individual/             # 独立策略文件
    ├── ma_cross_strategy.py
    ├── macd_cross_strategy.py
    ├── rsi_signal_strategy.py
    ├── bollinger_breakout_strategy.py
    ├── momentum_strategy.py
    ├── mean_reversion_strategy.py
    ├── breakout_strategy.py
    ├── turtle_strategy.py
    ├── kdj_signal_strategy.py
    └── kama_cross_strategy.py

使用示例：
    from strategies.bt_strategies.individual import MaCrossStrategy
    from strategies.bt_strategies.base_strategy import BaseCryptoStrategy

作者：量化交易团队
版本：1.1.0
"""

# 导入基类
from .base_strategy import BaseCryptoStrategy

# 导入工具函数
from .position_utils import get_position_mixin

# 导入所有独立策略
from .individual.ma_cross_strategy import MaCrossStrategy
from .individual.macd_cross_strategy import MacdCrossStrategy
from .individual.rsi_signal_strategy import RsiSignalStrategy
from .individual.bollinger_breakout_strategy import BollingerBreakoutStrategy
from .individual.momentum_strategy import MomentumStrategy
from .individual.mean_reversion_strategy import MeanReversionStrategy
from .individual.breakout_strategy import BreakoutStrategy
from .individual.turtle_strategy import TurtleStrategy
from .individual.kdj_signal_strategy import KdjSignalStrategy
from .individual.kama_cross_strategy import KamaCrossStrategy

# 策略映射（保持向后兼容）
STRATEGY_CLASSES = {
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

# 向后兼容：如果有人仍然直接导入类，可以直接使用
__all__ = [
    'BaseCryptoStrategy',
    'get_position_mixin',
    'MaCrossStrategy',
    'MacdCrossStrategy',
    'RsiSignalStrategy',
    'BollingerBreakoutStrategy',
    'MomentumStrategy',
    'MeanReversionStrategy',
    'BreakoutStrategy',
    'TurtleStrategy',
    'KdjSignalStrategy',
    'KamaCrossStrategy',
    'STRATEGY_CLASSES',
]
