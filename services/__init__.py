# -*- coding: utf-8 -*-
# Services Module
"""
统一服务层 - BACKEND
整合了所有服务层功能，按模块组织

架构特点：
- 统一的服务基类 (BaseService)
- 完整的服务接口定义 (IService)
- 强大的服务工厂 (ServiceFactory)
- 自动依赖注入
- 生命周期管理
- 配置管理
- 缓存支持
- 错误处理
- 性能监控

Modules:
- strategy: 策略服务
- analytics: 分析服务
- data_sync: 数据同步服务
- notification: 通知服务
- mcp: MCP服务
- scheduler: 调度服务
- config: 配置服务
- base: 基础服务类和接口
"""

# 导入基础服务架构
from .base.base_service import BaseService, ServiceMixin, ServiceConfig, ServiceContext
from .base.factory import ServiceFactory, get_service_factory, ServiceRegistry
from .base.interfaces import (
IService, IServiceConfig, ServiceStatus, ServiceType,
IStrategyService, IBacktestService,
IAnalysisService, IRiskManagementService, INotificationService,
ISchedulerService, IDataSyncService
)
from .base.service_validators import DataValidator, TradingValidator

# 导入统一ORM服务类
from .orm import (
    KlineDataServiceORM,
    CryptoMarketRankingsServiceORM,
    get_crypto_market_rankings_service_orm
)

# 暂时注释掉有问题的服务导入
# from .strategy.service import StrategyService
# from .strategy.backtest.service import BacktestService
# from .analytics.service import MarketAnalysisService
# from .analytics.technical.service import TechnicalAnalysisService
# from .data_sync.service import DataSyncService
# from .scheduler.service import SchedulerService

# 便捷函数
from .base.factory import (
get_strategy_service, get_backtest_service,
get_analysis_service, get_scheduler_service, get_data_sync_service
)

__all__ = [
# 基础架构
"BaseService",
"ServiceMixin",
"ServiceConfig",
"ServiceContext",
"ServiceFactory",
"ServiceRegistry",
"IService",
"IServiceConfig",
"ServiceStatus",
"ServiceType",

# 服务接口
"IStrategyService",
"IBacktestService",
"IAnalysisService",
"IRiskManagementService",
"INotificationService",
"ISchedulerService",
"IDataSyncService",

# 统一ORM服务类
"KlineDataServiceORM",
"CryptoMarketRankingsServiceORM",
"get_crypto_market_rankings_service_orm",
"NewsORM",

# 验证器
"DataValidator",
"TradingValidator",

# 服务工厂
"get_service_factory",

# 便捷函数
"get_strategy_service",
"get_backtest_service",
"get_analysis_service",
"get_scheduler_service",
"get_data_sync_service"
]

# 版本信息
__version__ = "2.0.0"
__author__ = "BACKEND Team"
__description__ = "统一服务层架构 - 提供完整的服务基础设施"