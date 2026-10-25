# -*- coding: utf-8 -*-
"""
统一ORM服务管理
提供所有ORM服务的统一导入接口
"""
from services.orm.crypto_market_rankings_orm import CryptoMarketRankingsServiceORM, \
    get_crypto_market_rankings_service_orm
from services.orm.kline_data_orm import KlineDataServiceORM
from services.orm.crypto_hourly_kline_orm import CryptoHourlyKlineORM, get_crypto_hourly_kline_orm
from services.orm.us_stocks_fundamental_orm import USStockFundamentalORM, get_us_stock_fundamental_orm

__all__ = [
    # 市场数据ORM服务
    'KlineDataServiceORM',

    # 同步数据ORM服务
    'CryptoMarketRankingsServiceORM',
    'get_crypto_market_rankings_service_orm',

    # 加密货币小时K线ORM服务
    'CryptoHourlyKlineORM',
    'get_crypto_hourly_kline_orm',

    # 美股基本面ORM服务
    'USStockFundamentalORM',
    'get_us_stock_fundamental_orm',
]
