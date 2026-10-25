# -*- coding: utf-8 -*-
"""
时间格式化工具
"""

from datetime import datetime
from typing import Union, Optional


def format_datetime(dt: Union[datetime, str, None], format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """
    格式化时间为指定格式
    
    Args:
        dt: 时间对象或字符串
        format_str: 格式字符串，默认为 "YYYY-MM-DD HH:mm:SS"
        
    Returns:
        str: 格式化后的时间字符串，如果输入为None则返回None
    """
    if dt is None:
        return None
    
    if isinstance(dt, str):
        try:
            # 尝试解析ISO格式
            if 'T' in dt:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(dt, format_str)
        except ValueError:
            return str(dt)
    
    if isinstance(dt, datetime):
        return dt.strftime(format_str)
    
    return str(dt)


def format_timestamp(timestamp: Union[datetime, str, None]) -> Optional[str]:
    """
    格式化时间戳为标准格式 YYYY-MM-DD HH:mm:SS
    
    Args:
        timestamp: 时间戳
        
    Returns:
        str: 格式化后的时间字符串
    """
    return format_datetime(timestamp)


def format_iso_datetime(dt: Union[datetime, str, None]) -> Optional[str]:
    """
    格式化时间为ISO格式但使用空格而不是T分隔
    
    Args:
        dt: 时间对象
        
    Returns:
        str: 格式化后的时间字符串
    """
    if dt is None:
        return None
    
    if isinstance(dt, str):
        try:
            if 'T' in dt:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            else:
                return dt
        except ValueError:
            return dt
    
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    return str(dt)
