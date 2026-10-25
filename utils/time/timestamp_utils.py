"""
时间戳工具模块
统一处理各种时间戳格式的转换和标准化
"""

from typing import Union, Optional
from datetime import datetime, timezone
import time


# 时间戳类型定义
Timestamp = Union[int, float, datetime, str]


class TimestampConverter:
    """时间戳转换器"""
    
    @staticmethod
    def to_milliseconds(timestamp: Timestamp) -> int:
        """
        将各种时间戳格式统一为毫秒级整数
        
        Args:
            timestamp: 时间戳，支持int, float, datetime, str格式
            
        Returns:
            int: 毫秒级时间戳
            
        Raises:
            ValueError: 无法解析的时间戳格式
        """
        if isinstance(timestamp, datetime):
            # datetime对象转换为毫秒时间戳
            if timestamp.tzinfo is None:
                # 如果没有时区信息，假设为UTC
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            return int(timestamp.timestamp() * 1000)
        
        elif isinstance(timestamp, (int, float)):
            # 数字时间戳
            ts_int = int(timestamp)
            
            # 判断是秒级还是毫秒级时间戳
            if ts_int < 10000000000:  # 小于10位数字，认为是秒级
                return ts_int * 1000
            else:  # 10位或以上，认为是毫秒级
                return ts_int
        
        elif isinstance(timestamp, str):
            # 字符串时间戳
            try:
                # 尝试解析为数字
                ts_float = float(timestamp)
                return TimestampConverter.to_milliseconds(ts_float)
            except ValueError:
                # 尝试解析为datetime字符串
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    return TimestampConverter.to_milliseconds(dt)
                except ValueError:
                    raise ValueError(f"无法解析时间戳字符串: {timestamp}")
        
        else:
            raise ValueError(f"不支持的时间戳类型: {type(timestamp)}")
    
    @staticmethod
    def to_seconds(timestamp: Timestamp) -> int:
        """
        将各种时间戳格式统一为秒级整数
        
        Args:
            timestamp: 时间戳，支持int, float, datetime, str格式
            
        Returns:
            int: 秒级时间戳
        """
        milliseconds = TimestampConverter.to_milliseconds(timestamp)
        return milliseconds // 1000
    
    @staticmethod
    def to_datetime(timestamp: Timestamp, tz: Optional[timezone] = None) -> datetime:
        """
        将各种时间戳格式统一为datetime对象
        
        Args:
            timestamp: 时间戳，支持int, float, datetime, str格式
            tz: 时区，默认为UTC
            
        Returns:
            datetime: 标准化的datetime对象
        """
        if isinstance(timestamp, datetime):
            if timestamp.tzinfo is None:
                return timestamp.replace(tzinfo=tz or timezone.utc)
            return timestamp
        
        milliseconds = TimestampConverter.to_milliseconds(timestamp)
        seconds = milliseconds / 1000.0
        
        if tz is None:
            tz = timezone.utc
        
        return datetime.fromtimestamp(seconds, tz=tz)
    
    @staticmethod
    def to_display_format(timestamp: Timestamp, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        将时间戳转换为显示格式字符串
        
        Args:
            timestamp: 时间戳
            format_str: 格式字符串，默认为 "YYYY-mm-DD HH:MM:SS"
            
        Returns:
            str: 格式化的时间字符串
        """
        dt = TimestampConverter.to_datetime(timestamp)
        # 确保不包含微秒部分
        dt = dt.replace(microsecond=0)
        return dt.strftime(format_str)
    
    @staticmethod
    def from_display_format(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> int:
        """
        从显示格式字符串转换为毫秒时间戳
        
        Args:
            date_str: 日期时间字符串
            format_str: 格式字符串
            
        Returns:
            int: 毫秒级时间戳
        """
        dt = datetime.strptime(date_str, format_str)
        # 假设为UTC时间
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return TimestampConverter.to_milliseconds(dt)
    
    @staticmethod
    def is_valid_timestamp(timestamp: Timestamp) -> bool:
        """
        检查时间戳是否有效
        
        Args:
            timestamp: 要检查的时间戳
            
        Returns:
            bool: 是否有效
        """
        try:
            TimestampConverter.to_milliseconds(timestamp)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def get_current_timestamp_ms() -> int:
        """获取当前时间的毫秒时间戳"""
        return int(time.time() * 1000)
    
    @staticmethod
    def get_current_timestamp_s() -> int:
        """获取当前时间的秒时间戳"""
        return int(time.time())
    
    @staticmethod
    def get_current_display_time() -> str:
        """获取当前时间的显示格式"""
        return TimestampConverter.to_display_format(TimestampConverter.get_current_timestamp_ms())
    
    @staticmethod
    def get_current_datetime_for_db() -> datetime:
        """获取当前时间用于数据库存储（精确到秒，不包含微秒）"""
        now = datetime.now()
        return now.replace(microsecond=0)
    
    @staticmethod
    def format_datetime_for_db(dt: datetime) -> datetime:
        """格式化datetime对象用于数据库存储（去除微秒）"""
        return dt.replace(microsecond=0)


# 便捷函数
def normalize_timestamp(timestamp: Timestamp) -> int:
    """将时间戳标准化为毫秒级整数"""
    return TimestampConverter.to_milliseconds(timestamp)


def timestamp_to_display(timestamp: Timestamp, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """将时间戳转换为显示格式"""
    return TimestampConverter.to_display_format(timestamp, format_str)


def display_to_timestamp(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> int:
    """将显示格式转换为毫秒时间戳"""
    return TimestampConverter.from_display_format(date_str, format_str)


def timestamp_to_datetime(timestamp: Timestamp, tz: Optional[timezone] = None) -> datetime:
    """将时间戳转换为datetime对象"""
    return TimestampConverter.to_datetime(timestamp, tz)


def datetime_to_timestamp(dt: datetime) -> int:
    """将datetime对象转换为毫秒时间戳"""
    return TimestampConverter.to_milliseconds(dt)


def is_valid_timestamp(timestamp: Timestamp) -> bool:
    """检查时间戳是否有效"""
    return TimestampConverter.is_valid_timestamp(timestamp)


# 时间戳常量
class TimestampConstants:
    """时间戳相关常量"""
    
    # 时间戳格式
    MILLISECONDS_PER_SECOND = 1000
    SECONDS_PER_MINUTE = 60
    SECONDS_PER_HOUR = 3600
    SECONDS_PER_DAY = 86400
    
    # 时间戳范围检查
    MIN_TIMESTAMP_MS = 0  # 1970-01-01 00:00:00 UTC
    MAX_TIMESTAMP_MS = 4102444800000  # 2100-01-01 00:00:00 UTC
    
    # 常用时间间隔（毫秒）
    ONE_MINUTE_MS = 60 * 1000
    ONE_HOUR_MS = 60 * 60 * 1000
    ONE_DAY_MS = 24 * 60 * 60 * 1000
    ONE_WEEK_MS = 7 * 24 * 60 * 60 * 1000
    ONE_MONTH_MS = 30 * 24 * 60 * 60 * 1000
    ONE_YEAR_MS = 365 * 24 * 60 * 60 * 1000
    
    # 显示格式常量
    DISPLAY_FORMAT = "%Y-%m-%d %H:%M:%S"
    DISPLAY_FORMAT_WITH_MS = "%Y-%m-%d %H:%M:%S.%f"
    DISPLAY_FORMAT_DATE_ONLY = "%Y-%m-%d"
    DISPLAY_FORMAT_TIME_ONLY = "%H:%M:%S"


# 数据库和API专用的时间戳处理
class DatabaseTimestampHandler:
    """数据库时间戳处理器"""
    
    @staticmethod
    def to_database_format(timestamp: Timestamp) -> str:
        """
        转换为数据库存储格式 (YYYY-mm-DD HH:MM:SS)
        
        Args:
            timestamp: 时间戳
            
        Returns:
            str: 数据库格式的时间字符串
        """
        return TimestampConverter.to_display_format(timestamp, TimestampConstants.DISPLAY_FORMAT)
    
    @staticmethod
    def from_database_format(date_str: str) -> int:
        """
        从数据库格式转换为毫秒时间戳
        
        Args:
            date_str: 数据库格式的时间字符串
            
        Returns:
            int: 毫秒级时间戳
        """
        return TimestampConverter.from_display_format(date_str, TimestampConstants.DISPLAY_FORMAT)


class APITimestampHandler:
    """API时间戳处理器"""
    
    @staticmethod
    def to_api_format(timestamp: Timestamp) -> str:
        """
        转换为API响应格式 (YYYY-mm-DD HH:MM:SS)
        
        Args:
            timestamp: 时间戳
            
        Returns:
            str: API格式的时间字符串
        """
        return TimestampConverter.to_display_format(timestamp, TimestampConstants.DISPLAY_FORMAT)
    
    @staticmethod
    def from_api_format(date_str: str) -> int:
        """
        从API格式转换为毫秒时间戳
        
        Args:
            date_str: API格式的时间字符串
            
        Returns:
            int: 毫秒级时间戳
        """
        return TimestampConverter.from_display_format(date_str, TimestampConstants.DISPLAY_FORMAT)
    
    @staticmethod
    def to_api_response(timestamp: Timestamp) -> dict:
        """
        转换为API响应格式，包含多种时间格式
        
        Args:
            timestamp: 时间戳
            
        Returns:
            dict: 包含多种时间格式的字典
        """
        dt = TimestampConverter.to_datetime(timestamp)
        ms_timestamp = TimestampConverter.to_milliseconds(timestamp)
        
        return {
            "timestamp_ms": ms_timestamp,
            "timestamp_s": ms_timestamp // 1000,
            "datetime": TimestampConverter.to_display_format(timestamp),
            "iso_format": dt.isoformat(),
            "utc_offset": dt.strftime("%z")
        }
