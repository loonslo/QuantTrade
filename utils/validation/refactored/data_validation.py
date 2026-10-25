"""
量化交易系统 - 验证器模块（重构后）
========================================

重构说明:
- 原始文件: utils/validation/validators.py (695行)
- 拆分后: 多个独立模块，平均每个 < 200行
- 职责分离: 每个模块专注特定验证类型
- 易于维护: 修改不影响其他模块

作者：量化交易团队
版本：1.1.0
"""

import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from ..core.logger_manager import get_logger


# 类 DataValidator 未找到


def validate_symbol(symbol: str) -> bool:
    """
    验证交易对格式
    
    Args:
        symbol: 交易对，如 'BTC/USDT'
        
    Returns:
        bool: 是否有效
    """
    if not isinstance(symbol, str):
        return False
    
    # 检查格式：BASE/QUOTE
    if '/' not in symbol:
        return False
    
    base, quote = symbol.split('/', 1)
    
    # 检查基础货币和报价货币
    if not base or not quote:
        return False
    
    # 检查长度（通常3-10个字符）
    if len(base) < 1 or len(base) > 10 or len(quote) < 1 or len(quote) > 10:
        return False
    
    # 检查字符（只允许字母和数字）
    if not base.isalnum() or not quote.isalnum():
        return False
    
    return True


def validate_timeframe(timeframe: str) -> bool:
    """
    验证时间周期格式
    
    Args:
        timeframe: 时间周期，如 '1m', '5m', '1h', '1d'
        
    Returns:
        bool: 是否有效
    """
    if not isinstance(timeframe, str):
        return False
    
    # 支持的时间周期
    valid_timeframes = [
        '1m', '3m', '5m', '15m', '30m',  # 分钟
        '1h', '2h', '4h', '6h', '8h', '12h',  # 小时
        '1d', '3d', '1w', '1M'  # 天、周、月
    ]
    
    return timeframe in valid_timeframes


def validate_amount(amount: float, min_amount: float = 0.0, max_amount: float = float('inf')) -> bool:
    """
    验证数量
    
    Args:
        amount: 数量
        min_amount: 最小数量
        max_amount: 最大数量
        
    Returns:
        bool: 是否有效
    """
    if not isinstance(amount, (int, float)):
        return False
    
    if amount < min_amount:
        return False
    
    if amount > max_amount:
        return False
    
    return True


# 通用验证工具
class UniversalValidator:
    """通用验证器"""
    
