# -*- coding: utf-8 -*-
"""
基础仓储类
提供统一的仓储基类和接口
"""

from typing import TypeVar, Generic, Optional, List, Dict, Any, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func
from abc import ABC, abstractmethod

from data.database.session_manager import get_session_manager
from utils.core.logger_manager import get_logger
from data.models.base.base_model import BaseModel

T = TypeVar('T', bound=BaseModel)


class IRepository(ABC):
    """仓储接口"""
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[BaseModel]:
        """根据ID获取实体"""
        pass
    
    @abstractmethod
    async def get_all(self, limit: Optional[int] = None) -> List[BaseModel]:
        """获取所有实体"""
        pass
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> BaseModel:
        """创建实体"""
        pass
    
    @abstractmethod
    async def update(self, id: int, data: Dict[str, Any]) -> Optional[BaseModel]:
        """更新实体"""
        pass
    
    @abstractmethod
    async def delete(self, id: int) -> bool:
        """删除实体"""
        pass


class ICrudRepository(IRepository, ABC):
    """CRUD仓储接口"""
    pass


class IMarketDataRepository(ABC):
    """市场数据仓储接口"""
    
    @abstractmethod
    async def get_kline_data(self, symbol: str, timeframe: str, limit: int) -> List[T]:
        """获取K线数据"""
        pass


class IStrategyRepository(ABC):
    """策略仓储接口"""
    pass


class IBacktestRepository(ABC):
    """回测仓储接口"""
    pass


class BaseRepository(Generic[T]):
    """基础仓储类"""
    
    def __init__(self, model_class: type, repository_name: str):
        """
        初始化仓储
        
        Args:
            model_class: 模型类
            repository_name: 仓储名称
        """
        self.model_class = model_class
        self.repository_name = repository_name
        self.logger = get_logger(repository_name)
        self.session_manager = get_session_manager()
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.session_manager.get_session()
    
    async def get_by_id(self, id: int) -> Optional[BaseModel]:
        """根据ID获取实体"""
        try:
            with self.get_session() as session:
                return session.query(self.model_class).filter(
                    self.model_class.id == id,
                    self.model_class.is_valid == True
                ).first()
        except Exception as e:
            self.logger.error(f"根据ID获取实体失败: {id}, {str(e)}")
            return None
    
    async def get_all(self, limit: Optional[int] = None) -> List[BaseModel]:
        """获取所有实体"""
        try:
            with self.get_session() as session:
                query = session.query(self.model_class).filter(
                    self.model_class.is_valid == True
                ).order_by(desc(self.model_class.created_at))
                
                if limit:
                    query = query.limit(limit)
                
                return query.all()
        except Exception as e:
            self.logger.error(f"获取所有实体失败: {str(e)}")
            return []
    
    async def create(self, data: Dict[str, Any]) -> Optional[BaseModel]:
        """创建实体"""
        try:
            with self.get_session() as session:
                entity = self.model_class(**data)
                session.add(entity)
                session.commit()
                session.refresh(entity)
                return entity
        except Exception as e:
            self.logger.error(f"创建实体失败: {str(e)}")
            return None
    
    async def update(self, id: int, data: Dict[str, Any]) -> Optional[BaseModel]:
        """更新实体"""
        try:
            with self.get_session() as session:
                entity = session.query(self.model_class).filter(
                    self.model_class.id == id,
                    self.model_class.is_valid == True
                ).first()
                
                if not entity:
                    return None
                
                for key, value in data.items():
                    if hasattr(entity, key):
                        setattr(entity, key, value)
                
                entity.updated_at = datetime.now()
                session.commit()
                session.refresh(entity)
                return entity
        except Exception as e:
            self.logger.error(f"更新实体失败: {id}, {str(e)}")
            return None
    
    async def delete(self, id: int) -> bool:
        """删除实体（软删除）"""
        try:
            with self.get_session() as session:
                entity = session.query(self.model_class).filter(
                    self.model_class.id == id,
                    self.model_class.is_valid == True
                ).first()
                
                if not entity:
                    return False
                
                entity.is_valid = False
                entity.updated_at = datetime.now()
                session.commit()
                return True
        except Exception as e:
            self.logger.error(f"删除实体失败: {id}, {str(e)}")
            return False
    
    async def count(self) -> int:
        """获取实体数量"""
        try:
            with self.get_session() as session:
                return session.query(self.model_class).filter(
                    self.model_class.is_valid == True
                ).count()
        except Exception as e:
            self.logger.error(f"获取实体数量失败: {str(e)}")
            return 0


class CrudRepository(BaseRepository[T]):
    """CRUD仓储类"""
    pass


class RepositoryFactory:
    """仓储工厂基类"""
    pass


# 为了向后兼容，创建别名
Repository = BaseRepository
