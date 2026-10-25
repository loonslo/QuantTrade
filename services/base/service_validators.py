# -*- coding: utf-8 -*-
"""
数据验证器
提供统一的数据验证功能
"""

from typing import Dict, Any
import re


class DataValidator:
    """数据验证器"""

    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """验证交易对符号"""
        if not symbol or not isinstance(symbol, str):
            return False
        # 基本格式验证
        pattern = r'^[A-Z]{2,10}[A-Z]{2,10}$'
        return bool(re.match(pattern, symbol))

    @staticmethod
    def validate_price(price: float) -> bool:
        """验证价格"""
        return isinstance(price, (int, float)) and price > 0

    @staticmethod
    def validate_volume(volume: float) -> bool:
        """验证成交量"""
        return isinstance(volume, (int, float)) and volume >= 0

    @staticmethod
    def validate_timestamp(timestamp: int) -> bool:
        """验证时间戳"""
        return isinstance(timestamp, int) and timestamp > 0

class TradingValidator:
    """交易验证器"""

    @staticmethod
    def validate_order_params(params: Dict[str, Any]) -> bool:
        """验证订单参数"""
        required_fields = ['symbol', 'side', 'type', 'quantity']

        for field in required_fields:
            if field not in params:
                return False

        # 验证具体字段
        if not DataValidator.validate_symbol(params['symbol']):
            return False

        if params['side'] not in ['buy', 'sell']:
            return False

        if params['type'] not in ['market', 'limit']:
            return False

        if not isinstance(params['quantity'], (int, float)) or params['quantity'] <= 0:
            return False

        return True

    @staticmethod
    def validate_strategy_params(params: Dict[str, Any]) -> bool:
        """验证策略参数"""
        if not isinstance(params, dict):
            return False

        # 基本参数验证
        if 'strategy_name' not in params:
            return False

        return True