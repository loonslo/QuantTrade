# -*- coding: utf-8 -*-
"""
基础服务类
提供统一的服务接口和基础功能
"""

from typing import Dict, Any, Optional, TypeVar
from datetime import datetime
from abc import ABC

from utils.core.logger_manager import get_logger
from services.base.interfaces.service_interfaces import ServiceStatus

T = TypeVar('T')

class ServiceConfig:
    """服务配置类"""

    def __init__(self,
                 timeout: int = 30,
                 retry_count: int = 3,
                 retry_delay: float = 1.0):
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay

class ServiceContext:
    """服务上下文"""

    def __init__(self, service_name: str, config: ServiceConfig):
        self.service_name = service_name
        self.config = config
        self.start_time = datetime.now()
        self.metadata: Dict[str, Any] = {}

class BaseService(ABC):
    """基础服务类"""

    def __init__(self, service_name: str = None, config: ServiceConfig = None):
        self.service_name = service_name or self.__class__.__name__
        self.config = config or ServiceConfig()
        self.logger = get_logger(f"service.{self.service_name}")
        self.context = ServiceContext(self.service_name, self.config)
        self._initialized = False
        self._services: Dict[str, 'BaseService'] = {}
        
        # 仓储管理
        self._repositories: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """初始化服务"""
        if self._initialized:
            return
        self.logger.info(f"初始化服务: {self.service_name}")
        
        # 调用子类的初始化钩子
        if hasattr(self, '_on_initialize'):
            await self._on_initialize()
        
        self._initialized = True

    async def start(self) -> None:
        """启动服务"""
        self.logger.info(f"启动服务: {self.service_name}")

    async def stop(self) -> None:
        """停止服务"""
        self.logger.info(f"停止服务: {self.service_name}")

    async def cleanup(self) -> None:
        """清理服务"""
        self.logger.info(f"清理服务: {self.service_name}")

    def get_status(self) -> ServiceStatus:
        """获取服务状态"""
        if not self._initialized:
            return ServiceStatus.INITIALIZING
        return ServiceStatus.RUNNING

    def set_service(self, name: str, service: 'BaseService') -> None:
        """设置依赖服务"""
        self._services[name] = service

    def get_service(self, name: str) -> Optional['BaseService']:
        """获取依赖服务"""
        return self._services.get(name)
    
    # 仓储管理方法
    def set_repository(self, name: str, repository: Any) -> None:
        """设置仓储"""
        self._repositories[name] = repository
    
    def get_repository(self, name: str) -> Optional[Any]:
        """获取仓储"""
        return self._repositories.get(name)

class ServiceMixin:
    """服务混入类"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def log_info(self, message: str) -> None:
        """记录信息日志"""
        self.logger.info(message)

    def log_error(self, message: str, error: Exception = None) -> None:
        """记录错误日志"""
        if error:
            self.logger.error(f"{message}: {error}")
        else:
            self.logger.error(message)