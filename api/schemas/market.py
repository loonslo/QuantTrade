# -*- coding: utf-8 -*-
"""
市场数据API请求模型
定义市场相关的所有Pydantic请求模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class MarketListRequest(BaseModel):
    """
    市场总览请求模型

    用于批量查询多个币种的市场数据，支持一次查询多个交易对
    """
    symbols: Optional[List[str]] = Field(
        default=None,
        description="币种符号列表，用于批量查询，最多支持 50 个交易对",
        example=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
        json_schema_extra={
            "description": "要查询的币种交易对符号数组，每个元素为标准交易对格式，如 'BTCUSDT' 表示比特币对 USDT 交易对。可选参数，不传则返回默认的 BTCUSDT 和 ETHUSDT 数据。最多支持 50 个交易对。"
        }
    )


class KlineDataRequest(BaseModel):
    """
    K线数据请求模型

    用于获取指定币种和时间框架的OHLCV（开高低收成交量）数据
    支持多种时间框架，可指定时间范围和返回条数
    """
    symbol: str = Field(
        ...,
        description="币种交易对符号",
        example="BTCUSDT",
        json_schema_extra={
            "description": "要查询的币种交易对符号，必须参数。格式为 '基础货币+计价货币'，如 'BTCUSDT' 表示比特币对 USDT 的交易对。",
            "minLength": 6,
            "maxLength": 20
        }
    )
    timeframe: str = Field(
        ...,
        description="时间框架（K线周期）",
        example="1h",
        json_schema_extra={
            "description": "K线数据的时间框架周期，影响数据的粒度和范围。可选值：1m(1分钟)、5m(5分钟)、15m(15分钟)、30m(30分钟)、1h(1小时)、2h(2小时)、4h(4小时)、6h(6小时)、8h(8小时)、12h(12小时)、1d(1天)、1w(1周)、1M(1月)。必须参数。",
            "enum": ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "1w", "1M"]
        }
    )
    start: Optional[str] = Field(
        default=None,
        description="开始时间",
        example="2025-11-05 00:00:00",
        json_schema_extra={
            "description": "查询的起始时间，格式为 'YYYY-MM-DD HH:MM:SS'。可选参数，与end一起使用。当指定start和end时，会自动计算并返回指定时间范围内的所有数据，忽略limit参数。建议使用 UTC 时间。",
            "pattern": "^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}$"
        }
    )
    end: Optional[str] = Field(
        default=None,
        description="结束时间",
        example="2025-11-05 10:00:00",
        json_schema_extra={
            "description": "查询的结束时间，格式为 'YYYY-MM-DD HH:MM:SS'。可选参数，与start一起使用。当指定start和end时，会自动计算并返回指定时间范围内的所有数据，忽略limit参数。建议使用 UTC 时间。",
            "pattern": "^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}$"
        }
    )
    limit: Optional[int] = Field(
        default=100,
        description="返回数据条数限制",
        example=100,
        ge=1,
        le=1000,
        json_schema_extra={
            "description": f"要返回的K线数据条数，取值范围 1-1000。默认值 100 条。此参数仅在未指定start和end时生效。指定了start和end后，将忽略limit参数并返回整个时间范围内的所有数据。"
        }
    )


class TechnicalIndicatorsRequest(BaseModel):
    """
    技术指标请求模型

    用于计算和获取各种技术分析指标，包括RSI、MACD、布林带、移动平均线等
    帮助判断价格趋势和超买超卖状态
    """
    symbol: str = Field(
        ...,
        description="币种交易对符号",
        example="BTCUSDT",
        json_schema_extra={
            "description": "要查询的币种交易对符号，必须参数。格式为 '基础货币+计价货币'，如 'BTCUSDT' 表示比特币对 USDT 的交易对。",
            "minLength": 6,
            "maxLength": 20
        }
    )
    timeframe: str = Field(
        default="1h",
        description="时间框架（K线周期）",
        example="1h",
        json_schema_extra={
            "description": "K线数据的时间框架周期，影响技术指标计算的准确性。可选值：1m(1分钟)、5m(5分钟)、15m(15分钟)、30m(30分钟)、1h(1小时)、4h(4小时)、1d(1天)。默认值为 1h。较长时间框架的指标更稳定但滞后性更强。",
            "enum": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        }
    )


class TrendDataRequest(BaseModel):
    """
    趋势数据请求模型

    用于获取价格趋势分析数据，支持多币种对比和多个时间周期
    提供趋势方向、强度、变化百分比和波动率分析
    """
    symbol: Optional[str] = Field(
        default="BTCUSDT",
        description="币种交易对符号",
        example="BTCUSDT",
        json_schema_extra={
            "description": "要查询的币种交易对符号，可选参数。不传则使用默认值 BTCUSDT。格式为 '基础货币+计价货币'，如 'BTCUSDT' 表示比特币对 USDT 的交易对。目前版本只支持单个币种查询。",
            "minLength": 6,
            "maxLength": 20
        }
    )
    period: str = Field(
        default="7d",
        description="趋势分析周期",
        example="7d",
        json_schema_extra={
            "description": "趋势分析的时间周期长度，影响数据采集范围和分析结果的粒度。可选值：1d(1天，分析7小时数据)、7d(7天，分析30天数据)、30d(30天，分析90天数据)。默认值为 7d。",
            "enum": ["1d", "7d", "30d"]
        }
    )


class CryptoFuturesRequest(BaseModel):
    """
    期货市场数据请求模型

    用于获取永续合约的持仓量、资金费率、多空比例等期货特有指标
    提供期货市场情绪和资金流向分析
    """
    symbol: str = Field(
        ...,
        description="币种交易对符号",
        example="BTCUSDT",
        json_schema_extra={
            "description": "要查询的币种交易对符号，必须参数。注意：期货交易对通常以 USDT 计价，如 'BTCUSDT' 表示比特币永续合约。支持所有主流币种的永续合约交易对。",
            "minLength": 6,
            "maxLength": 20
        }
    )


class MarketRankRequest(BaseModel):
    """
    市场排行请求模型

    用于按交易量排序的加密货币排行榜
    提供市场热门币种排名、价格、涨跌幅、交易量和市值信息
    """
    limit: int = Field(
        default=20,
        description="返回数量限制",
        example=20,
        ge=1,
        le=100,
        json_schema_extra={
            "description": f"要返回的排行数据条数，取值范围 1-100。默认值 20 条。较大的值会增加响应时间，建议根据实际需求合理设置。排行榜按 24 小时交易量降序排列。",
        }
    )


class SupportResistanceRequest(BaseModel):
    """
    支撑阻力位请求模型

    用于分析价格图表，识别关键支撑位和阻力位，帮助交易决策
    """
    symbol: str = Field(
        ...,
        description="币种交易对符号",
        example="BTCUSDT",
        json_schema_extra={
            "description": "要查询的币种交易对符号，必须参数。格式为 '基础货币+计价货币'，如 'BTCUSDT' 表示比特币对 USDT 的交易对。支撑阻力位分析通常用于日线或更长时间框架。",
            "minLength": 6,
            "maxLength": 20
        }
    )
    timeframe: str = Field(
        default="1h",
        description="时间框架（K线周期）",
        example="1h",
        json_schema_extra={
            "description": "K线数据的时间框架周期，较长时间框架的支撑阻力位更可靠。可选值：1h(1小时)、4h(4小时)、1d(1天)、1w(1周)。默认值为 1h。建议使用4小时或日线进行更准确的分析。",
            "enum": ["1h", "4h", "1d", "1w"]
        }
    )


class CryptoIndicatorsRequest(BaseModel):
    """
    币圈原生指标请求模型

    用于获取币圈特有的技术指标，包括Supertrend、Heikin-Ashi、PSAR、VWAP等
    """
    symbol: str = Field(
        ...,
        description="币种交易对符号",
        example="BTCUSDT",
        json_schema_extra={
            "description": "要查询的币种交易对符号，必须参数。格式为 '基础货币+计价货币'，如 'BTCUSDT' 表示比特币对 USDT 的交易对。",
            "minLength": 6,
            "maxLength": 20
        }
    )
    timeframe: str = Field(
        default="1h",
        description="时间框架（K线周期）",
        example="1h",
        json_schema_extra={
            "description": "K线数据的时间框架周期，影响指标计算的准确性。可选值：1m(1分钟)、5m(5分钟)、15m(15分钟)、30m(30分钟)、1h(1小时)、4h(4小时)、1d(1天)。默认值为 1h。",
            "enum": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        }
    )
    indicator_type: str = Field(
        default="all",
        description="指标类型",
        example="all",
        json_schema_extra={
            "description": "要计算的指标类型。可选值：supertrend、heikin_ashi、psar、vwap、stoch_rsi、vw_macd、ema_ribbon、all。默认值为 all，返回所有指标。",
            "enum": ["supertrend", "heikin_ashi", "psar", "vwap", "stoch_rsi", "vw_macd", "ema_ribbon", "all"]
        }
    )


class ShortTemplateRequest(BaseModel):
    """
    短打模板请求模型

    用于获取币圈短打模板策略信号分析
    """
    symbol: str = Field(
        ...,
        description="币种交易对符号",
        example="BTCUSDT",
        json_schema_extra={
            "description": "要查询的币种交易对符号，必须参数。格式为 '基础货币+计价货币'，如 'BTCUSDT' 表示比特币对 USDT 的交易对。",
            "minLength": 6,
            "maxLength": 20
        }
    )
    timeframe: str = Field(
        default="1h",
        description="时间框架（K线周期）",
        example="1h",
        json_schema_extra={
            "description": "K线数据的时间框架周期，短打策略建议使用1小时或4小时。可选值：1h(1小时)、4h(4小时)。默认值为 1h。",
            "enum": ["1h", "4h"]
        }
    )


class FuturesDataRequest(BaseModel):
    """
    期货市场数据请求模型

    用于获取资金费率、未平仓量等期货特有指标
    """
    symbol: str = Field(
        ...,
        description="币种交易对符号",
        example="BTCUSDT",
        json_schema_extra={
            "description": "要查询的币种交易对符号，必须参数。格式为 '基础货币+计价货币'，如 'BTCUSDT' 表示比特币对 USDT 的永续合约。",
            "minLength": 6,
            "maxLength": 20
        }
    )


class OnChainDataRequest(BaseModel):
    """
    链上数据请求模型

    用于获取链上情绪指标，如净流入、SOPR、杠杆比率等
    """
    symbol: str = Field(
        default="BTC",
        description="币种符号",
        example="BTC",
        json_schema_extra={
            "description": "要查询的币种符号，可选参数。默认为 BTC。支持 BTC、ETH 等主流币种。",
            "minLength": 2,
            "maxLength": 10
        }
    )
    data_type: str = Field(
        default="all",
        description="数据类型",
        example="netflow",
        json_schema_extra={
            "description": "要查询的链上数据类型。可选值：netflow（净流入）、sopr（已实现盈亏比）、leverage_ratio（杠杆比率）、all（全部）。默认值为 all。",
            "enum": ["netflow", "sopr", "leverage_ratio", "all"]
        }
    )
