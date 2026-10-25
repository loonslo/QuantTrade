# -*- coding: utf-8 -*-
"""
数据转换器
提供数据格式化转换功能
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

class MarketDataTransformer:
    """市场数据转换器"""

    @staticmethod
    def format_coin_data(coin_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化单个币种数据"""
        if not coin_data:
            return {}

        result = {}
        if 'price' in coin_data and coin_data['price'] is not None:
            result["price"] = f"${coin_data['price']:,.2f}"
        if 'change_24h' in coin_data and coin_data['change_24h'] is not None:
            result["change_24h"] = f"{coin_data['change_24h']:.2f}%"
        if 'change_amount' in coin_data and coin_data['change_amount'] is not None:
            result["change_amount"] = f"${coin_data['change_amount']:,.2f}"
        if 'market_cap' in coin_data and coin_data['market_cap'] is not None:
            result["market_cap"] = f"${coin_data['market_cap']:,.0f}B"
        if 'volume_24h' in coin_data and coin_data['volume_24h'] is not None:
            result["volume_24h"] = f"${coin_data['volume_24h']:,.0f}B"
        if 'trend_chart_data' in coin_data and coin_data['trend_chart_data'] is not None:
            result["trend_chart_data"] = coin_data['trend_chart_data']

        return result

    @staticmethod
    def format_market_summary(overview_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化市场摘要数据"""
        if not overview_data:
            return {}

        result = {}
        if 'total_market_cap' in overview_data and overview_data['total_market_cap'] is not None:
            result["total_market_cap"] = f"${overview_data['total_market_cap']:,.0f}B"
        if 'total_volume_24h' in overview_data and overview_data['total_volume_24h'] is not None:
            result["total_volume_24h"] = f"${overview_data['total_volume_24h']:,.0f}B"
        if 'market_trend' in overview_data and overview_data['market_trend'] is not None:
            result["market_trend"] = overview_data['market_trend']
        if 'risk_level' in overview_data and overview_data['risk_level'] is not None:
            result["risk_level"] = overview_data['risk_level']
        if 'key_insights' in overview_data and overview_data['key_insights'] is not None:
            result["key_insights"] = overview_data['key_insights']

        return result

    @staticmethod
    def format_sentiment_data(fear_greed_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """格式化情绪数据"""
        if not fear_greed_data:
            return {}

        result = {}
        if 'value' in fear_greed_data and fear_greed_data['value'] is not None:
            value = fear_greed_data['value']
            result["fear_greed_index"] = value
            result["sentiment"] = MarketDataTransformer._get_sentiment_description(value)
            result["classification"] = MarketDataTransformer._get_sentiment_classification(value)
        if 'updated_at' in fear_greed_data and fear_greed_data['updated_at'] is not None:
            result["updated_at"] = fear_greed_data['updated_at']
        if 'trend' in fear_greed_data and fear_greed_data['trend'] is not None:
            result["trend"] = fear_greed_data['trend']

        return result

    @staticmethod
    def format_market_summary_from_symbols(symbols_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从币种数据生成市场摘要"""
        if not symbols_data:
            return {}

        result = {}

        # 计算总市值和交易量
        total_market_cap = sum(s.get('market_cap', 0) for s in symbols_data if s.get('market_cap') is not None)
        total_volume = sum(s.get('volume_24h', 0) for s in symbols_data if s.get('volume_24h') is not None)

        if total_market_cap > 0:
            result["total_market_cap"] = f"${total_market_cap:,.0f}B"
        if total_volume > 0:
            result["total_volume_24h"] = f"${total_volume:,.0f}B"

        # 生成关键洞察
        if symbols_data:
            result["key_insights"] = ["数据同步中"]

        return result

    @staticmethod
    def _get_sentiment_description(index: int) -> str:
        """获取情绪描述"""
        if index <= 25:
            return "极度恐惧"
        elif index <= 45:
            return "恐惧"
        elif index <= 55:
            return "中性"
        elif index <= 75:
            return "贪婪"
        else:
            return "极度贪婪"

    @staticmethod
    def _get_sentiment_classification(index: int) -> str:
        """获取情绪分类"""
        if index <= 25:
            return "Extreme Fear"
        elif index <= 45:
            return "Fear"
        elif index <= 55:
            return "Neutral"
        elif index <= 75:
            return "Greed"
        else:
            return "Extreme Greed"

class TechnicalAnalysisTransformer:
    """技术分析数据转换器"""

    @staticmethod
    def format_technical_indicators(indicators: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化技术指标"""
        if not indicators:
            return []

        formatted_indicators = []
        for indicator in indicators:
            if not indicator:
                continue

            formatted_indicator = {}
            if 'name' in indicator and indicator['name'] is not None:
                formatted_indicator["name"] = indicator['name']
            if 'value' in indicator and indicator['value'] is not None:
                formatted_indicator["value"] = indicator['value']
            if 'signal' in indicator and indicator['signal'] is not None:
                formatted_indicator["signal"] = indicator['signal']
            if 'strength' in indicator and indicator['strength'] is not None:
                formatted_indicator["strength"] = indicator['strength']

            # 生成描述
            if formatted_indicator:
                formatted_indicator["description"] = TechnicalAnalysisTransformer._get_indicator_description(indicator)
                formatted_indicators.append(formatted_indicator)

        return formatted_indicators

    @staticmethod
    def format_support_resistance_levels(levels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化支撑阻力位"""
        if not levels:
            return []

        formatted_levels = []
        for level in levels:
            if not level:
                continue

            formatted_level = {}
            if 'price' in level and level['price'] is not None:
                formatted_level["price"] = level['price']
            if 'level_type' in level and level['level_type'] is not None:
                formatted_level["level_type"] = level['level_type']
            if 'strength' in level and level['strength'] is not None:
                formatted_level["strength"] = level['strength']
            if 'touches' in level and level['touches'] is not None:
                formatted_level["touches"] = level['touches']
            if 'last_touch' in level and level['last_touch'] is not None:
                formatted_level["last_touch"] = level['last_touch']

            if formatted_level:
                formatted_levels.append(formatted_level)

        return formatted_levels

    @staticmethod
    def _get_indicator_description(indicator: Dict[str, Any]) -> str:
        """获取指标描述"""
        name = indicator.get("name", "")
        signal = indicator.get("signal", "hold")

        descriptions = {
            "RSI": {
                "buy": "RSI超卖区域，可能反弹",
                "sell": "RSI超买区域，可能回调",
                "hold": "RSI处于中性区域"
            },
            "MACD": {
                "buy": "MACD金叉信号，看涨",
                "sell": "MACD死叉信号，看跌",
                "hold": "MACD信号不明显"
            },
            "Bollinger Bands": {
                "buy": "价格触及下轨，可能反弹",
                "sell": "价格触及上轨，可能回调",
                "hold": "价格在中轨附近"
            }
        }

        return descriptions.get(name, {}).get(signal, "指标信号不明显")

class ResponseTransformer:
    """响应数据转换器"""

    @staticmethod
    def format_api_response(data: Any, message: str = "成功", success: bool = True) -> Dict[str, Any]:
        """格式化API响应"""
        return {
            "success": success,
            "data": data,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def format_error_response(error: str, data: Any = None) -> Dict[str, Any]:
        """格式化错误响应"""
        response = {
            "success": False,
            "message": error,
            "timestamp": datetime.now().isoformat()
        }
        if data is not None:
            response["data"] = data
        return response

    @staticmethod
    def format_paginated_response(data: List[Any], total: int, page: int, size: int) -> Dict[str, Any]:
        """格式化分页响应"""
        return {
            "success": True,
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size
            },
            "message": "成功获取分页数据",
            "timestamp": datetime.now().isoformat()
        }