# -*- coding: utf-8 -*-
"""
时间戳处理混入类
提供统一的时间戳字段管理和自动更新功能
"""

from datetime import datetime
from sqlalchemy import Column, DateTime, event
from sqlalchemy.ext.declarative import declared_attr

from utils.time.timestamp_utils import TimestampConverter


class AutoTimestampMixin:
    """
    自动时间戳混入类
    提供自动管理 created_at 和 updated_at 字段的功能
    """
    
    @declared_attr
    def created_at(cls):
        return Column(
            DateTime, 
            nullable=False, 
            default=TimestampConverter.get_current_datetime_for_db,
            comment='创建时间'
        )
    
    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime, 
            nullable=False, 
            default=TimestampConverter.get_current_datetime_for_db,
            onupdate=TimestampConverter.get_current_datetime_for_db,
            comment='更新时间'
        )
    
    def touch(self):
        """手动更新 updated_at 时间戳"""
        self.updated_at = TimestampConverter.get_current_datetime_for_db()
    
    def get_formatted_created_at(self) -> str:
        """获取格式化的创建时间"""
        return self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
    
    def get_formatted_updated_at(self) -> str:
        """获取格式化的更新时间"""
        return self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else ''


# 为所有使用 AutoTimestampMixin 的模型自动设置 updated_at
@event.listens_for(AutoTimestampMixin, 'before_update', propagate=True)
def receive_before_update(mapper, connection, target):
    """在更新前自动设置 updated_at"""
    target.updated_at = TimestampConverter.get_current_datetime_for_db()


@event.listens_for(AutoTimestampMixin, 'before_insert', propagate=True)
def receive_before_insert(mapper, connection, target):
    """在插入前自动设置时间戳"""
    current_time = TimestampConverter.get_current_datetime_for_db()
    if not target.created_at:
        target.created_at = current_time
    if not target.updated_at:
        target.updated_at = current_time