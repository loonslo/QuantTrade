"""
统一的数据库模型基类
所有SQLAlchemy模型都应该继承自这里的Base类
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, Boolean, String, Integer
from sqlalchemy.ext.declarative import declarative_base
import json

from utils.time.timestamp_utils import TimestampConverter
from .timestamp_mixin import AutoTimestampMixin

# 统一的Base类，所有SQLAlchemy模型都从这里继承
Base = declarative_base()


class TimestampMixin:
    """时间戳处理混入类，为数据库模型提供统一的时间戳处理方法"""

    def get_timestamp_ms(self, field_name: str = 'updated_at') -> int:
        """获取指定字段的毫秒时间戳"""
        dt = getattr(self, field_name)
        if dt is None:
            return 0
        return TimestampConverter.to_milliseconds(dt)

    def set_timestamp_from_ms(self, timestamp_ms: int, field_name: str = 'updated_at') -> None:
        """从毫秒时间戳设置指定字段"""
        dt = TimestampConverter.to_datetime(timestamp_ms)
        setattr(self, field_name, dt)

    def get_display_time(self, field_name: str = 'updated_at') -> str:
        """获取指定字段的显示格式时间"""
        dt = getattr(self, field_name)
        if dt is None:
            return ""
        return TimestampConverter.to_display_format(dt)

    def to_api_dict(self) -> dict:
        """转换为API响应格式的字典，包含时间戳的多种格式"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                timestamp_ms = TimestampConverter.to_milliseconds(value)
                result[column.name] = {
                    "datetime": TimestampConverter.to_display_format(value),
                    "timestamp_ms": timestamp_ms,
                    "timestamp_s": timestamp_ms // 1000,
                    "iso_format": value.isoformat()
                }
            else:
                result[column.name] = value
        return result


class BaseModel(Base, TimestampMixin, AutoTimestampMixin):
    """
    统一的基础模型类
    提供通用字段和方法
    """
    __abstract__ = True
    
    # 通用字段（时间戳字段由 AutoTimestampMixin 提供）
    is_valid = Column(Boolean, default=True, index=True, comment='是否有效')
    source = Column(String(50), default='system', comment='数据来源')
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat() if value else None
            else:
                result[column.name] = value
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude_fields: Optional[list] = None):
        """从字典更新模型"""
        exclude_fields = exclude_fields or ['id', 'created_at']
        
        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                setattr(self, key, value)
        
        # updated_at 会通过 AutoTimestampMixin 自动更新
    
    def set_metadata(self, data: Dict[str, Any], field_name: str = 'metadata'):
        """设置JSON元数据"""
        if hasattr(self, field_name):
            setattr(self, field_name, json.dumps(data, ensure_ascii=False))
    
    def get_metadata(self, field_name: str = 'metadata') -> Dict[str, Any]:
        """获取JSON元数据"""
        if hasattr(self, field_name):
            metadata_str = getattr(self, field_name)
            if metadata_str:
                try:
                    return json.loads(metadata_str)
                except json.JSONDecodeError:
                    return {}
        return {}
    
    def mark_invalid(self):
        """标记为无效"""
        self.is_valid = False
        # updated_at 会通过 AutoTimestampMixin 自动更新
    
    def mark_valid(self):
        """标记为有效"""
        self.is_valid = True
        # updated_at 会通过 AutoTimestampMixin 自动更新


class AuditMixin:
    """审计混入类，提供审计字段"""
    
    created_by = Column(String(50), comment='创建者')
    updated_by = Column(String(50), comment='更新者')
    version = Column(Integer, default=1, comment='版本号')
    
    def increment_version(self):
        """增加版本号"""
        self.version = (self.version or 0) + 1