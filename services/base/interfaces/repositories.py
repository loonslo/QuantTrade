# -*- coding: utf-8 -*-
"""
仓储接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TypeVar, Generic
from datetime import datetime

from .service_interfaces import IRepository

T = TypeVar('T')

class IMarketDataRepository(IRepository[T]):
    """市场数据仓储接口"""

    @abstractmethod
    async def get_latest_data(self, symbol: str) -> Optional[T]:
        """获取最新数据"""
        pass

    @abstractmethod
    async def get_historical_data(self, symbol: str, start_time: datetime, end_time: datetime) -> List[T]:
        """获取历史数据"""
        pass

class IKlineDataRepository(IRepository[T]):
    """K线数据仓储接口"""

    @abstractmethod
    async def get_kline_data(self, symbol: str, timeframe: str, limit: int) -> List[T]:
        """获取K线数据"""
        pass

class ICoinDetailsRepository(IRepository[T]):
    """币种详情仓储接口"""

    @abstractmethod
    async def get_coin_details(self, symbol: str) -> Optional[T]:
        """获取币种详情"""
        pass

class IStrategyRepository(IRepository[T]):
    """策略仓储接口"""

    @abstractmethod
    async def get_strategy(self, strategy_name: str) -> Optional[T]:
        """获取策略"""
        pass

class IBacktestRepository(IRepository[T]):
    """回测仓储接口"""

    @abstractmethod
    async def get_backtest_result(self, backtest_id: str) -> Optional[T]:
        """获取回测结果"""
        pass

class IUserRepository(IRepository[T]):
    """用户仓储接口"""

    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[T]:
        """获取用户"""
        pass