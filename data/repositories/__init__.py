"""
统一数据仓储层
提供统一的数据访问接口和实现

包含以下仓储模块:
- base/: 基础仓储接口和通用功能
- market_data/: 市场数据仓储
- strategy/: 策略和交易记录仓储
- backtest/: 回测仓储
- analytics/: 分析仓储（支撑阻力位等）
- sync/: 同步仓储（恐慌贪婪等）
"""

# 基础仓储类
from .repository_base import (
    BaseRepository,
    CrudRepository,
    RepositoryFactory,
    IRepository,
    ICrudRepository,
    IMarketDataRepository,
    IStrategyRepository,
    IBacktestRepository
)

# 市场数据仓储
from .market_data import (
    MarketDataRepositoryFactory,
    FearGreedRepository,
    CoinDetailsRepository,
    MarketOverviewRepository,
    KlineDataRepository,
    PopularCoinsRepository
)

# 策略仓储
from .strategy import (
    StrategyRepositoryFactory,
    TradeRecordsRepository
)

# 回测仓储
from .backtest import (
    BacktestRepository,
    BacktestRepositoryFactory
)

# 分析仓储
from .analytics import (
    SupportResistanceRepository
)

# 同步仓储
from .sync import (
    FearGreedRepository
)

__all__ = [
    # 基础仓储类
    "Repository",
    "CrudRepository",
    "RepositoryFactory",
    "IRepository",
    "ICrudRepository",
    "IMarketDataRepository",
    "IStrategyRepository",
    "IBacktestRepository",
    
    # 市场数据仓储
    "MarketDataRepository",
    "MarketDataRepositoryFactory",
    "CoinDetailsRepository",
    
    # 策略仓储
    "StrategyRepository",
    "StrategyRepositoryFactory",
    
    # 回测仓储
    "BacktestRepository",
    "BacktestRepositoryFactory",
    
    # 分析仓储
    "SupportResistanceRepository",
    
    # 同步仓储
    "FearGreedRepository"
]