# -*- coding: utf-8 -*-
"""
基础接口定义
定义服务、仓储等核心接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TypeVar, Generic
from datetime import datetime
from enum import Enum

class ServiceStatus(Enum):
    """服务状态枚举"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class ServiceType(Enum):
    """服务类型枚举"""
    MARKET_DATA = "market_data"
    STRATEGY = "strategy"
    BACKTEST = "backtest"
    ANALYSIS = "analysis"
    SCHEDULER = "scheduler"
    DATA_SYNC = "data_sync"
    MCP = "mcp"

class IServiceConfig(ABC):
    """服务配置接口"""

    @abstractmethod
    def get_timeout(self) -> int:
        """获取超时时间"""
        pass

    @abstractmethod
    def get_retry_count(self) -> int:
        """获取重试次数"""
        pass

class IService(ABC):
    """服务接口"""

    @abstractmethod
    async def initialize(self) -> None:
        """初始化服务"""
        pass

    @abstractmethod
    async def start(self) -> None:
        """启动服务"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """停止服务"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """清理服务"""
        pass

    @abstractmethod
    def get_status(self) -> ServiceStatus:
        """获取服务状态"""
        pass

T = TypeVar('T')

class IRepository(ABC, Generic[T]):
    """仓储接口"""

    @abstractmethod
    async def get_by_id(self, id: Any) -> Optional[T]:
        """根据ID获取实体"""
        pass

    @abstractmethod
    async def save(self, entity: T) -> T:
        """保存实体"""
        pass

    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """删除实体"""
        pass

    @abstractmethod
    async def find_all(self) -> List[T]:
        """查找所有实体"""
        pass

class IDataProvider(ABC):
    """数据提供者接口"""

    @abstractmethod
    async def get_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取数据"""
        pass

    @abstractmethod
    async def validate_data(self, data: Dict[str, Any]) -> bool:
        """验证数据"""
        pass