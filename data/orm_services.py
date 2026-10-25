# -*- coding: utf-8 -*-
"""
数据ORM服务
提供统一的ORM数据服务接口
"""

from typing import Optional, Any, Dict

# 全局服务实例
# K线服务按参数维度缓存，避免首参固化问题
_kline_data_services: Dict[bool, Any] = {}
_market_overview_service: Optional[Any] = None
_crypto_market_rankings_service: Optional[Any] = None
_trading_signals_service: Optional[Any] = None
_support_resistance_service: Optional[Any] = None
_indicators_cache_service: Optional[Any] = None
_news_service: Optional[Any] = None


def get_kline_data_service(use_timeframe_tables: bool = True):
    """获取K线数据服务实例（按 use_timeframe_tables 参数区分缓存）"""
    service = _kline_data_services.get(use_timeframe_tables)
    if service is None:
        # 延迟导入避免循环依赖
        from services import KlineDataServiceORM
        service = KlineDataServiceORM(use_timeframe_tables=use_timeframe_tables)
        _kline_data_services[use_timeframe_tables] = service
    return service


def get_crypto_market_rankings_service():
    """获取加密货币市场排行服务实例"""
    global _crypto_market_rankings_service
    if _crypto_market_rankings_service is None:
        # 延迟导入避免循环依赖
        from services.orm.crypto_market_rankings_orm import get_crypto_market_rankings_service_orm
        _crypto_market_rankings_service = get_crypto_market_rankings_service_orm()
    return _crypto_market_rankings_service


def get_market_overview_service():
    """获取市场概览服务实例"""
    global _market_overview_service
    if _market_overview_service is None:
        # 延迟导入避免循环依赖
        from services.orm.market_overview_orm import get_market_overview_service_orm
        _market_overview_service = get_market_overview_service_orm()
    return _market_overview_service


def get_trading_signals_service():
    """获取交易信号服务实例"""
    global _trading_signals_service
    if _trading_signals_service is None:
        # 延迟导入避免循环依赖
        from services.orm.trading_signals_orm import get_trading_signals_service_orm
        _trading_signals_service = get_trading_signals_service_orm()
    return _trading_signals_service


def get_support_resistance_service():
    """获取支撑阻力服务实例"""
    global _support_resistance_service
    if _support_resistance_service is None:
        # 延迟导入避免循环依赖
        from services.orm.support_resistance_orm import get_support_resistance_service_orm
        _support_resistance_service = get_support_resistance_service_orm()
    return _support_resistance_service


def get_news_service():
    """获取新闻数据服务实例"""
    global _news_service
    if _news_service is None:
        # 延迟导入避免循环依赖
        from services.orm.news_orm import NewsORM
        _news_service = NewsORM()
    return _news_service


def get_us_market_service():
    """获取美国市场数据服务实例"""
    from services.orm.us_market_orm import get_us_market_service_orm
    return get_us_market_service_orm()


def get_exchange_rate_service():
    """获取汇率数据服务实例"""
    from services.orm.us_market_orm import get_exchange_rate_service_orm
    return get_exchange_rate_service_orm()


def get_qdii_fund_service():
    """获取QDII基金数据服务实例"""
    from services.orm.qdii_fund_orm import get_qdii_fund_service_orm
    return get_qdii_fund_service_orm()


def get_us_stocks_service():
    """获取美股个股数据服务实例"""
    from services.orm.us_stocks_orm import get_us_stocks_service
    return get_us_stocks_service()


# 导出可用的服务获取函数
__all__ = [
    'get_kline_data_service',
    'get_crypto_market_rankings_service',
    'get_market_overview_service',
    'get_trading_signals_service',
    'get_support_resistance_service',
    'get_news_service',
    'get_us_market_service',
    'get_exchange_rate_service',
    'get_qdii_fund_service',
    'get_us_stocks_service',
]
