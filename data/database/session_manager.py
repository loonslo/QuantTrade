"""
SQLAlchemy Session管理器
提供统一的数据库会话管理和ORM操作支持
"""

from typing import Optional, Type, TypeVar, List, Dict, Any
from contextlib import contextmanager
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session

from utils.core.logger_manager import get_logger
from data.models.base.base_model import Base
from data.database_init_service import get_database_init_service

# 泛型类型变量
ModelType = TypeVar('ModelType', bound=Base)


class DatabaseSessionManager:
    """数据库会话管理器"""

    def __init__(self):
        self.logger = get_logger('database_session_manager')
        self.db_service = get_database_init_service()
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._scoped_session: Optional[scoped_session] = None
        self._initialize()

    def _initialize(self):
        """初始化数据库连接和会话工厂"""
        try:
            self._engine = self.db_service._get_engine()
            self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)
            self._scoped_session = scoped_session(self._session_factory)
            self.logger.info("数据库会话管理器初始化成功")
        except Exception as e:
            self.logger.error(f"数据库会话管理器初始化失败: {e}")
            raise

    @property
    def engine(self) -> Engine:
        """获取数据库引擎"""
        return self._engine

    def get_session(self) -> Session:
        """获取新的数据库会话"""
        return self._session_factory()

    def get_scoped_session(self) -> scoped_session:
        """获取范围会话（线程安全）"""
        return self._scoped_session

    @contextmanager
    def session_scope(self, auto_commit: bool = True):
        """
        会话上下文管理器

        Args:
            auto_commit: 是否自动提交事务

        Yields:
            Session: 数据库会话对象
        """
        session = self.get_session()
        try:
            yield session
            if auto_commit:
                session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"数据库会话异常: {e}")
            raise
        finally:
            session.close()

    def create_all_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(self._engine)
            self.logger.info("所有表创建成功")
        except Exception as e:
            self.logger.error(f"创建表失败: {e}")
            raise

    def drop_all_tables(self):
        """删除所有表（谨慎使用）"""
        try:
            Base.metadata.drop_all(self._engine)
            self.logger.warning("所有表已删除")
        except Exception as e:
            self.logger.error(f"删除表失败: {e}")
            raise

    def close_all_sessions(self):
        """关闭所有会话"""
        try:
            if self._scoped_session:
                self._scoped_session.remove()
            self.logger.info("所有会话已关闭")
        except Exception as e:
            self.logger.error(f"关闭会话失败: {e}")


class ORMBaseService:
    """ORM基础服务类"""

    def __init__(self, service_name: str):
        self.logger = get_logger(service_name)
        self.service_name = service_name
        self.session_manager = get_session_manager()

    @contextmanager
    def get_db_session(self, auto_commit: bool = True):
        """获取数据库会话上下文"""
        with self.session_manager.session_scope(auto_commit=auto_commit) as session:
            yield session

    def create_record(self, model_class: Type[ModelType], **kwargs) -> Optional[ModelType]:
        """
        创建新记录

        Args:
            model_class: 模型类
            **kwargs: 字段值

        Returns:
            创建的模型实例
        """
        try:
            with self.get_db_session() as session:
                instance = model_class(**kwargs)
                session.add(instance)
                session.flush()  # 获取生成的ID
                session.refresh(instance)  # 刷新实例
                return instance
        except Exception as e:
            self.logger.error(f"创建记录失败: {e}")
            return None

    def get_record_by_id(self, model_class: Type[ModelType], record_id: int) -> Optional[ModelType]:
        """
        根据ID获取记录

        Args:
            model_class: 模型类
            record_id: 记录ID

        Returns:
            模型实例或None
        """
        try:
            with self.get_db_session(auto_commit=False) as session:
                return session.query(model_class).filter(model_class.id == record_id).first()
        except Exception as e:
            self.logger.error(f"获取记录失败: {e}")
            return None

    def get_records_by_filter(self, model_class: Type[ModelType], **filters) -> List[ModelType]:
        """
        根据过滤条件获取记录列表

        Args:
            model_class: 模型类
            **filters: 过滤条件

        Returns:
            模型实例列表
        """
        try:
            with self.get_db_session(auto_commit=False) as session:
                query = session.query(model_class)
                for field, value in filters.items():
                    if hasattr(model_class, field):
                        query = query.filter(getattr(model_class, field) == value)
                return query.all()
        except Exception as e:
            self.logger.error(f"获取记录列表失败: {e}")
            return []

    def update_record(self, model_class: Type[ModelType], record_id: int, **kwargs) -> bool:
        """
        更新记录

        Args:
            model_class: 模型类
            record_id: 记录ID
            **kwargs: 更新字段

        Returns:
            更新是否成功
        """
        try:
            with self.get_db_session() as session:
                record = session.query(model_class).filter(model_class.id == record_id).first()
                if record:
                    for field, value in kwargs.items():
                        if hasattr(record, field):
                            setattr(record, field, value)
                    return True
                return False
        except Exception as e:
            self.logger.error(f"更新记录失败: {e}")
            return False

    def delete_record(self, model_class: Type[ModelType], record_id: int) -> bool:
        """
        删除记录

        Args:
            model_class: 模型类
            record_id: 记录ID

        Returns:
            删除是否成功
        """
        try:
            with self.get_db_session() as session:
                record = session.query(model_class).filter(model_class.id == record_id).first()
                if record:
                    session.delete(record)
                    return True
                return False
        except Exception as e:
            self.logger.error(f"删除记录失败: {e}")
            return False

    def soft_delete_records(self, model_class: Type[ModelType], **filters) -> int:
        """
        软删除记录（设置is_valid=0）

        Args:
            model_class: 模型类
            **filters: 过滤条件

        Returns:
            影响的记录数
        """
        try:
            with self.get_db_session() as session:
                query = session.query(model_class)
                for field, value in filters.items():
                    if hasattr(model_class, field):
                        query = query.filter(getattr(model_class, field) == value)

                # 只有模型有is_valid字段才执行软删除
                if hasattr(model_class, 'is_valid'):
                    count = query.update({'is_valid': False})
                    return count
                else:
                    self.logger.warning(f"{model_class.__name__} 模型没有is_valid字段，无法执行软删除")
                    return 0
        except Exception as e:
            self.logger.error(f"软删除记录失败: {e}")
            return 0

    def count_records(self, model_class: Type[ModelType], **filters) -> int:
        """
        统计记录数量

        Args:
            model_class: 模型类
            **filters: 过滤条件

        Returns:
            记录数量
        """
        try:
            with self.get_db_session(auto_commit=False) as session:
                query = session.query(model_class)
                for field, value in filters.items():
                    if hasattr(model_class, field):
                        query = query.filter(getattr(model_class, field) == value)
                return query.count()
        except Exception as e:
            self.logger.error(f"统计记录数量失败: {e}")
            return 0

    def bulk_create_records(self, model_class: Type[ModelType], records_data: List[Dict[str, Any]]) -> bool:
        """
        批量创建记录

        Args:
            model_class: 模型类
            records_data: 记录数据列表

        Returns:
            创建是否成功
        """
        try:
            with self.get_db_session() as session:
                instances = [model_class(**data) for data in records_data]
                session.add_all(instances)
                return True
        except Exception as e:
            self.logger.error(f"批量创建记录失败: {e}")
            return False


# 全局会话管理器实例
_session_manager: Optional[DatabaseSessionManager] = None


def get_session_manager() -> DatabaseSessionManager:
    """获取全局会话管理器实例（单例模式）"""
    global _session_manager
    if _session_manager is None:
        _session_manager = DatabaseSessionManager()
    return _session_manager


def get_db_session() -> Session:
    """快捷方式：获取数据库会话"""
    return get_session_manager().get_session()


def get_scoped_session() -> scoped_session:
    """快捷方式：获取范围会话"""
    return get_session_manager().get_scoped_session()
