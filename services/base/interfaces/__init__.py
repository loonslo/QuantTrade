# -*- coding: utf-8 -*-
"""
服务基础接口模块
提供服务层的基础接口定义
"""

from .service_interfaces import IService, IServiceConfig, ServiceStatus, IRepository, IDataProvider
from .services import (
IStrategyService, IBacktestService,
IAnalysisService, IRiskManagementService, INotificationService,
ISchedulerService, IDataSyncService, ServiceType
)
from .repositories import (
IRepository, IMarketDataRepository, IStrategyRepository,
IBacktestRepository, IUserRepository
)

__all__ = [
# 基础接口
"IService",
"IServiceConfig",
"ServiceStatus",
"IRepository",
"IDataProvider",

# 服务接口
"IStrategyService",
"IBacktestService",
"IAnalysisService",
"IRiskManagementService",
"INotificationService",
"ISchedulerService",
"IDataSyncService",
"ServiceType",

# 仓储接口
"IMarketDataRepository",
"IStrategyRepository",
"IBacktestRepository",
"IUserRepository"
]