# -*- coding: utf-8 -*-
"""
ORM 服务基类
提供统一的数据操作方法，自动处理时间戳字段
"""

from typing import Dict, Any, Optional, List, Type
from datetime import datetime
from sqlalchemy import and_

from services.data_sync.base_service import DataSyncService
from data.models.base.base_model import BaseModel


class BaseORMService(DataSyncService):
    """
    ORM 服务基类
    提供统一的 CRUD 操作，自动处理时间戳字段
    """

    def __init__(self, service_name: str, model_class: Type[BaseModel]):
        """
        初始化 ORM 服务

        Args:
            service_name: 服务名称
            model_class: 对应的模型类
        """
        super().__init__(service_name)
        self.model_class = model_class

    def create_model_record(self, data: Dict[str, Any], **kwargs) -> Optional[BaseModel]:
        """
        创建新记录

        Args:
            data: 记录数据
            **kwargs: 额外的字段值

        Returns:
            创建的记录实例或 None
        """
        try:
            with self.session_manager.session_scope() as session:
                # 合并数据和额外参数
                record_data = {**data, **kwargs}

                # 移除不属于模型的字段
                filtered_data = self._filter_model_fields(record_data)

                # 创建记录（时间戳字段会自动设置）
                record = self.model_class(**filtered_data)
                session.add(record)
                session.flush()
                session.refresh(record)
                return record

        except Exception as e:
            self.logger.error("创建记录失败: {}".format(e))
            return None

    def update_model_record(self, record_id: int, data: Dict[str, Any]) -> bool:
        """
        更新记录

        Args:
            record_id: 记录ID
            data: 更新数据

        Returns:
            更新是否成功
        """
        try:
            with self.session_manager.session_scope() as session:
                record = session.query(self.model_class).filter(
                    self.model_class.id == record_id
                ).first()

                if not record:
                    self.logger.warning("记录不存在: ID={}".format(record_id))
                    return False

                # 过滤字段并更新
                filtered_data = self._filter_model_fields(data)
                for key, value in filtered_data.items():
                    if key != 'created_at':  # 不更新创建时间
                        setattr(record, key, value)

                return True

        except Exception as e:
            self.logger.error("更新记录失败: {}".format(e))
            return False

    def upsert_record(self,
                      filter_conditions: Dict[str, Any],
                      data: Dict[str, Any],
                      **kwargs) -> Optional[BaseModel]:
        """
        插入或更新记录
        
        Args:
            filter_conditions: 查找条件
            data: 记录数据
            **kwargs: 额外的字段值
            
        Returns:
            记录实例或 None
        """
        try:
            with self.get_db_session() as session:
                return self._upsert_with_session(session, filter_conditions, data, **kwargs)
        except Exception as e:
            self.logger.error("Upsert 记录失败: {}".format(e))
            return None

    def _upsert_with_session(
            self,
            session,
            filter_conditions: Dict[str, Any],
            data: Dict[str, Any],
            **kwargs,
    ) -> Optional[BaseModel]:
        """
        在给定的 Session 内执行 upsert，供单条和批量调用复用。
        """
        # 查找现有记录
        query = session.query(self.model_class)
        for key, value in filter_conditions.items():
            query = query.filter(getattr(self.model_class, key) == value)

        existing_record = query.first()

        # 合并数据
        record_data = {**data, **kwargs}
        filtered_data = self._filter_model_fields(record_data)

        if existing_record:
            # 更新现有记录
            for key, value in filtered_data.items():
                if key != 'created_at':  # 保持原创建时间
                    setattr(existing_record, key, value)
            return existing_record

        # 创建新记录
        new_record = self.model_class(**filtered_data)
        session.add(new_record)
        session.flush()
        return new_record

    def batch_upsert(self, records: List[Dict[str, Any]],
                     unique_fields: List[str], **common_kwargs) -> bool:
        """
        批量插入或更新记录
        
        Args:
            records: 记录列表
            unique_fields: 用于判断唯一性的字段列表
            **common_kwargs: 所有记录共同的字段值
            
        Returns:
            操作是否成功
        """
        try:
            with self.get_db_session() as session:
                success_count = 0

                for record_data in records:
                    # 构建查找条件
                    filter_conditions = {}
                    for field in unique_fields:
                        if field in record_data:
                            filter_conditions[field] = record_data[field]
                        elif field in common_kwargs:
                            filter_conditions[field] = common_kwargs[field]

                    if not filter_conditions:
                        self.logger.warning("跳过记录，缺少唯一字段: {}".format(unique_fields))
                        continue

                    # 在同一 Session 内执行 upsert
                    result = self._upsert_with_session(
                        session, filter_conditions, record_data, **common_kwargs
                    )
                    if result:
                        success_count += 1

                return success_count == len(records)

        except Exception as e:
            self.logger.error("批量 upsert 失败: {}".format(e))
            return False

    def mark_invalid_by_conditions(self, conditions: Dict[str, Any]) -> int:
        """
        根据条件标记记录为无效
        
        Args:
            conditions: 查找条件
            
        Returns:
            更新的记录数量
        """
        try:
            with self.get_db_session() as session:
                query = session.query(self.model_class)

                # 构建查询条件
                filter_conditions = []
                for key, value in conditions.items():
                    filter_conditions.append(getattr(self.model_class, key) == value)

                if filter_conditions:
                    query = query.filter(and_(*filter_conditions))

                # 更新为无效，尽量同时更新更新时间（若存在）
                update_values = {"is_valid": False}
                if hasattr(self.model_class, 'updated_at'):
                    update_values["updated_at"] = datetime.utcnow()

                updated_count = query.update(update_values, synchronize_session=False)

                return updated_count

        except Exception as e:
            self.logger.error("标记无效记录失败: {}".format(e))
            return 0

    def get_model_record_by_id(self, record_id: int) -> Optional[BaseModel]:
        """根据ID获取记录"""
        try:
            with self.get_db_session(auto_commit=False) as session:
                return session.query(self.model_class).filter(
                    self.model_class.id == record_id
                ).first()
        except Exception as e:
            self.logger.error("获取记录失败: {}".format(e))
            return None

    def get_record_by_id(self, model_class, record_id: int) -> Optional[BaseModel]:
        try:
            with self.get_db_session(auto_commit=False) as session:
                return session.query(model_class).filter(model_class.id == record_id).first()
        except Exception as e:
            self.logger.error("获取记录失败: {}".format(e))
            return None

    def get_model_records_by_conditions(self,
                                        conditions: Dict[str, Any],
                                        limit: Optional[int] = None,
                                        order_by: Optional[str] = None,
                                        only_valid: bool = True) -> List[BaseModel]:
        """
        根据条件获取记录列表
        
        Args:
            conditions: 查找条件
            limit: 记录数量限制
            order_by: 排序字段
            only_valid: 是否只获取有效记录
            
        Returns:
            记录列表
        """
        try:
            with self.get_db_session(auto_commit=False) as session:
                query = self._build_query(session, conditions, only_valid, order_by, limit)
                return query.all()

        except Exception as e:
            self.logger.error("获取记录列表失败: {}".format(e))
            return []

    def get_records_by_filter(self, model_class, **filters) -> List[BaseModel]:
        try:
            with self.get_db_session(auto_commit=False) as session:
                query = session.query(model_class)
                for field, value in filters.items():
                    if hasattr(model_class, field):
                        query = query.filter(getattr(model_class, field) == value)
                return query.all()
        except Exception as e:
            self.logger.error("获取记录列表失败: {}".format(e))
            return []

    def _filter_model_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        过滤出模型中存在的字段
        
        Args:
            data: 原始数据
            
        Returns:
            过滤后的数据
        """
        if not hasattr(self.model_class, '__table__'):
            return data

        model_columns = {col.name for col in self.model_class.__table__.columns}
        return {k: v for k, v in data.items() if k in model_columns}

    def get_model_record_count(self,
                               conditions: Optional[Dict[str, Any]] = None,
                               only_valid: bool = True) -> int:
        """
        获取记录数量
        
        Args:
            conditions: 查找条件
            only_valid: 是否只统计有效记录
            
        Returns:
            记录数量
        """
        try:
            with self.get_db_session(auto_commit=False) as session:
                query = self._build_query(session, conditions or {}, only_valid)
                return query.count()

        except Exception as e:
            self.logger.error("获取记录数量失败: {}".format(e))
            return 0

    # 删除多签名兼容路由后，统一使用 update_model_record

    def _build_query(self, session, conditions: Dict[str, Any], only_valid: bool,
                     order_by: Optional[str] = None, limit: Optional[int] = None):
        """
        构建通用查询，避免重复的过滤/排序/限制逻辑。
        """
        query = session.query(self.model_class)

        filter_conditions = []
        for key, value in conditions.items():
            filter_conditions.append(getattr(self.model_class, key) == value)

        if only_valid:
            is_valid_col = getattr(self.model_class, 'is_valid', None)
            if is_valid_col is not None:
                filter_conditions.append(is_valid_col.is_(True))

        if filter_conditions:
            query = query.filter(and_(*filter_conditions))

        if order_by:
            if hasattr(self.model_class, order_by):
                query = query.order_by(getattr(self.model_class, order_by))

        if limit:
            query = query.limit(limit)

        return query


    # 满足抽象方法要求，提供默认实现
    async def _execute_sync(self):
        return None

    def get_task_config(self) -> Dict[str, Any]:
        return {
            "service_name": self.service_name,
            "enabled": True
        }
