"""
通用数据模型
定义API中通用的请求和响应模型
"""

from pydantic import BaseModel, Field, field_serializer, ConfigDict
from typing import Dict, Any, Optional, Union
from datetime import datetime
import pytz
from utils.time.timestamp_utils import TimestampConverter, Timestamp, normalize_timestamp


class BaseModelWithDateTime(BaseModel):
    """包含时间字段序列化的基础模型类，支持指定时区"""
    
    model_config = ConfigDict(
        # 优化序列化性能
        str_strip_whitespace=True,
        validate_assignment=True,
        # 使用更高效的序列化模式
        ser_json_timedelta='iso8601',
        ser_json_bytes='base64'
    )
    
    def __init__(self, **data):
        # 允许在初始化时指定目标时区，默认为东八区
        self._target_timezone = data.pop('_target_timezone', 'Asia/Shanghai')
        super().__init__(**data)
    
    @field_serializer('*', check_fields=False)
    def serialize_datetime_fields(self, value: Any, field_name: str) -> Any:
        """
        统一序列化时间字段为 YYYY-MM-DD HH:MM:SS 格式
        自动转换到指定的时区
        """
        if isinstance(value, datetime):
            try:
                # 获取目标时区
                target_tz = pytz.timezone(self._target_timezone)
                
                # 处理时区信息
                if value.tzinfo is not None:
                    # 如果有时区信息，转换到目标时区
                    value = value.astimezone(target_tz)
                else:
                    # 如果没有时区信息，假设为UTC时间
                    utc_tz = pytz.UTC
                    value = utc_tz.localize(value).astimezone(target_tz)
                
                return value.strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                # 如果时区转换失败，返回原始格式
                return value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, (int, float)):
            # 处理时间戳格式
            try:
                dt = TimestampConverter.to_datetime(value)
                return TimestampConverter.to_display_format(dt)
            except Exception:
                return str(value)
        return value
    
    @classmethod
    def get_current_time(cls, timezone_name: str = 'Asia/Shanghai') -> datetime:
        """
        获取当前时间（指定时区）
        
        Args:
            timezone_name: 时区名称，默认东八区
            
        Returns:
            datetime: 当前时间
        """
        tz = pytz.timezone(timezone_name)
        return datetime.now(tz)
    
    @classmethod
    def format_datetime_for_db(cls, dt: datetime = None, timezone_name: str = 'Asia/Shanghai') -> str:
        """
        格式化时间字符串用于数据库存储
        
        Args:
            dt: datetime对象，如果为None则使用当前时间
            timezone_name: 时区名称
            
        Returns:
            str: 格式化后的时间字符串
        """
        if dt is None:
            dt = cls.get_current_time(timezone_name)
        
        # 处理时区
        if dt.tzinfo is None:
            # 如果没有时区信息，假设为UTC
            dt = pytz.UTC.localize(dt)
        
        # 转换到目标时区
        target_tz = pytz.timezone(timezone_name)
        dt = dt.astimezone(target_tz)
        
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    def get_timestamp_ms(self, field_name: str = 'created_at') -> int:
        """
        获取指定字段的毫秒时间戳
        
        Args:
            field_name: 字段名称
            
        Returns:
            int: 毫秒级时间戳
        """
        value = getattr(self, field_name, None)
        if value is None:
            return 0
        return normalize_timestamp(value)
    
    def set_timestamp_from_ms(self, timestamp_ms: int, field_name: str = 'created_at') -> None:
        """
        从毫秒时间戳设置指定字段
        
        Args:
            timestamp_ms: 毫秒级时间戳
            field_name: 字段名称
        """
        dt = TimestampConverter.to_datetime(timestamp_ms)
        setattr(self, field_name, dt)
    
    def get_display_time(self, field_name: str = 'created_at') -> str:
        """
        获取指定字段的显示格式时间
        
        Args:
            field_name: 字段名称
            
        Returns:
            str: 显示格式的时间字符串 (YYYY-mm-DD HH:MM:SS)
        """
        value = getattr(self, field_name, None)
        if value is None:
            return ""
        return TimestampConverter.to_display_format(value)
    
    def to_api_response(self) -> dict:
        """
        转换为API响应格式，包含时间戳的多种格式
        
        Returns:
            dict: 包含时间戳信息的字典
        """
        result = {}
        for field_name, field_info in self.model_fields.items():
            value = getattr(self, field_name, None)
            if isinstance(value, datetime):
                # 对于datetime字段，提供多种时间格式
                timestamp_ms = TimestampConverter.to_milliseconds(value)
                result[field_name] = {
                    "datetime": TimestampConverter.to_display_format(value),
                    "timestamp_ms": timestamp_ms,
                    "timestamp_s": timestamp_ms // 1000,
                    "iso_format": value.isoformat()
                }
            elif isinstance(value, (int, float)) and 'time' in field_name.lower():
                # 对于可能是时间戳的数值字段
                try:
                    timestamp_ms = normalize_timestamp(value)
                    dt = TimestampConverter.to_datetime(timestamp_ms)
                    result[field_name] = {
                        "datetime": TimestampConverter.to_display_format(dt),
                        "timestamp_ms": timestamp_ms,
                        "timestamp_s": timestamp_ms // 1000,
                        "iso_format": dt.isoformat()
                    }
                except Exception:
                    result[field_name] = value
            else:
                result[field_name] = value
        return result


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PaginationRequest(BaseModel):
    """分页请求模型"""
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页大小")


class PaginationResponse(BaseModel):
    """分页响应模型"""
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool


class TimeRangeRequest(BaseModelWithDateTime):
    """时间范围请求模型"""
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")


class ApiInfo(BaseModel):
    """API信息模型"""
    name: str
    version: str
    description: str
    status: str = "running" 