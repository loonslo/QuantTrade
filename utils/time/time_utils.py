"""
时区转换工具
提供统一的时区转换功能，确保所有时间显示为东八区（北京时间）
"""

from datetime import datetime, timezone, timedelta
from typing import Union


def to_beijing_time(dt: Union[datetime, str, None]) -> str:
    """
    将时间转换为东八区（北京时间）字符串
    
    Args:
        dt: 时间对象或字符串
        
    Returns:
        str: 东八区时间字符串，格式为 "YYYY-MM-DD HH:MM:SS"（不包含时区信息）
    """
    if dt is None:
        return "未知时间"
    
    if isinstance(dt, str):
        try:
            # 尝试解析字符串为datetime
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return str(dt)
    
    if not isinstance(dt, datetime):
        return str(dt)
    
    try:
        # 如果是UTC时间，转换为东八区
        if dt.tzinfo is None:
            # 假设是UTC时间，转换为东八区
            utc_time = dt.replace(tzinfo=timezone.utc)
            beijing_tz = timezone(timedelta(hours=8))
            beijing_time = utc_time.astimezone(beijing_tz)
            # 返回不带时区信息的时间字符串
            return beijing_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # 如果已经有时区信息，转换为东八区
            beijing_tz = timezone(timedelta(hours=8))
            beijing_time = dt.astimezone(beijing_tz)
            # 返回不带时区信息的时间字符串
            return beijing_time.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        # 如果转换失败，返回原始时间字符串（不包含时区信息）
        if hasattr(dt, 'strftime'):
            # 如果是datetime对象，确保不包含时区信息
            if dt.tzinfo is not None:
                # 如果有时区信息，先转换为本地时间再格式化
                local_time = dt.astimezone().replace(tzinfo=None)
                return local_time.strftime("%Y-%m-%d %H:%M:%S")
            else:
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return str(dt)


def get_beijing_timezone() -> timezone:
    """
    获取东八区时区对象
    
    Returns:
        timezone: 东八区时区对象
    """
    return timezone(timedelta(hours=8))


def is_utc_time(dt: datetime) -> bool:
    """
    判断时间是否为UTC时间
    
    Args:
        dt: 时间对象
        
    Returns:
        bool: 是否为UTC时间
    """
    return dt.tzinfo == timezone.utc


def is_beijing_time(dt: datetime) -> bool:
    """
    判断时间是否为东八区时间
    
    Args:
        dt: 时间对象
        
    Returns:
        bool: 是否为东八区时间
    """
    beijing_tz = timezone(timedelta(hours=8))
    return dt.tzinfo == beijing_tz 