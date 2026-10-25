# -*- coding: utf-8 -*-
"""
服务相关接口定义
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from .service_interfaces import ServiceStatus, IService

class ServiceType(Enum):
    """服务类型枚举"""
    MARKET_DATA = "market_data"
    STRATEGY = "strategy"
    BACKTEST = "backtest"
    ANALYSIS = "analysis"
    SCHEDULER = "scheduler"
    DATA_SYNC = "data_sync"
    MCP = "mcp"

class IAnalysisService(IService):
    """分析服务接口"""

    @abstractmethod
    async def analyze_market(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """分析市场"""
        pass

class IStrategyService(IService):
    """策略服务接口"""

    @abstractmethod
    async def execute_strategy(self, strategy_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行策略"""
        pass

class IBacktestService(IService):
    """回测服务接口"""

    @abstractmethod
    async def run_backtest(self, strategy_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """运行回测"""
        pass

class IRiskManagementService(IService):
    """风险管理服务接口"""

    @abstractmethod
    async def assess_risk(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险"""
        pass

class INotificationService(IService):
    """通知服务接口"""

    @abstractmethod
    async def send_notification(self, message: str, channel: str) -> bool:
        """发送通知"""
        pass

class ISchedulerService(IService):
    """调度服务接口"""

    @abstractmethod
    async def schedule_task(self, task_name: str, params: Dict[str, Any]) -> bool:
        """调度任务"""
        pass

class IDataSyncService(IService):
    """数据同步服务接口"""

    @abstractmethod
    async def sync_data(self, data_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """同步数据"""
        pass