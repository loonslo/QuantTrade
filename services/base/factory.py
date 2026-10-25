# -*- coding: utf-8 -*-
"""
统一服务工厂
提供服务的创建、管理和依赖注入功能
"""

from typing import Dict, Any, Type, TypeVar, Optional, Callable, List
from datetime import datetime
import asyncio
from enum import Enum

from utils.core.config_manager import config_manager
from utils.core.logger_manager import get_logger
from .base_service import BaseService, ServiceConfig
from .interfaces import IService, ServiceStatus, ServiceType

T = TypeVar('T', bound=BaseService)

class ServiceRegistry:
    """服务注册表"""

    def __init__(self):
        self._services: Dict[str, Type[BaseService]] = {}
        self._instances: Dict[str, BaseService] = {}
        self._configs: Dict[str, ServiceConfig] = {}
        self._dependencies: Dict[str, List[str]] = {}
        self.logger = get_logger("service_registry")

    def register(self,
                 service_name: str,
                 service_class: Type[BaseService],
                 config: Optional[ServiceConfig] = None,
                 dependencies: Optional[List[str]] = None) -> None:
        """注册服务"""
        self._services[service_name] = service_class
        self._configs[service_name] = config or ServiceConfig()
        self._dependencies[service_name] = dependencies or []
        self.logger.info(f"注册服务: {service_name}")

    def get_service_class(self, service_name: str) -> Optional[Type[BaseService]]:
        """获取服务类"""
        return self._services.get(service_name)

    def list_services(self) -> List[str]:
        """列出所有已注册的服务"""
        return list(self._services.keys())

class ServiceFactory:
    """统一服务工厂"""

    def __init__(self):
        self.config = config_manager
        self.logger = get_logger("service_factory")
        self.registry = ServiceRegistry()
        self._initialized = False
        self._instances: Dict[str, BaseService] = {}

    async def initialize(self) -> None:
        """初始化服务工厂"""
        if self._initialized:
            return
        self.logger.info("初始化服务工厂")
        self._initialized = True

    async def get_service(self, service_name: str) -> Optional[BaseService]:
        """获取服务实例"""
        if service_name in self._instances:
            return self._instances[service_name]
        return None

# 全局服务工厂实例
_service_factory: Optional[ServiceFactory] = None

async def get_service_factory() -> ServiceFactory:
    """获取全局服务工厂实例"""
    global _service_factory
    if _service_factory is None:
        _service_factory = ServiceFactory()
        await _service_factory.initialize()
    return _service_factory

# 便捷函数
async def get_strategy_service():
    """获取策略服务"""
    factory = await get_service_factory()
    return await factory.get_service("strategy")

async def get_backtest_service():
    """获取回测服务"""
    factory = await get_service_factory()
    return await factory.get_service("backtest")

async def get_analysis_service():
    """获取分析服务"""
    factory = await get_service_factory()
    return await factory.get_service("analysis")

async def get_scheduler_service():
    """获取调度服务"""
    factory = await get_service_factory()
    return await factory.get_service("scheduler")

async def get_data_sync_service():
    """获取数据同步服务"""
    factory = await get_service_factory()
    return await factory.get_service("data_sync")