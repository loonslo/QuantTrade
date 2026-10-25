# -*- coding: utf-8 -*-
"""
市场数据API路由
提供市场数据查询接口
"""

from fastapi import APIRouter, Query, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd

from services.orm.kline_data_orm import KlineDataServiceORM
from services.orm.market_overview_orm import get_market_overview_service_orm, MarketOverviewServiceORM
from services.crypto_indicators.crypto_indicators import CryptoIndicators, OnChainIndicators, FuturesIndicators
from api.schemas.market import (
    MarketListRequest, KlineDataRequest, TechnicalIndicatorsRequest, TrendDataRequest,
    CryptoFuturesRequest, MarketRankRequest, SupportResistanceRequest,
    CryptoIndicatorsRequest, ShortTemplateRequest, FuturesDataRequest, OnChainDataRequest
)
from api.middleware.response_formatter import ResponseFormatter

router = APIRouter()
response_handler = ResponseFormatter()

# 服务实例
kline_service = KlineDataServiceORM()
market_overview_service: MarketOverviewServiceORM = get_market_overview_service_orm()


@router.post("/market/list")
async def get_market_list(
    request: MarketListRequest
):
    """
    获取市场总览数据

    批量查询多个加密货币的市场概况信息，包括当前价格、24小时涨跌幅、交易量等关键数据。

    ## 功能特点
    - 支持批量查询，一次最多可查询 50 个交易对
    - 返回实时或近实时的市场数据
    - 单个交易对查询失败不会影响其他交易对的返回
    - 默认返回 BTCUSDT 和 ETHUSDT 的数据

    ## 返回数据说明
    每个交易对返回的数据包括：
    - 交易对符号和币种名称
    - 当前价格（USDT 计价）
    - 24 小时价格变化（绝对值和百分比）
    - 24 小时最高价和最低价
    - 24 小时交易量
    - 最后更新时间

    ## 使用场景
    适用于市场概览页面、多币种监控面板、热门币种展示等场景。
    """
    try:
        # 从请求体中提取参数
        symbols = request.symbols

        # 默认获取BTCUSDT和ETHUSDT
        if not symbols:
            symbols = ["BTCUSDT", "ETHUSDT"]

        # 设置时间范围：最近24小时
        from datetime import datetime, timedelta
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

        result = []

        for symbol in symbols:
            try:
                # 获取1h K线数据作为基础
                df = kline_service.load_kline_data(
                    symbol=symbol,
                    timeframe="1h",
                    start_time=start_time,
                    end_time=end_time,
                    limit=1
                )

                if df.empty:
                    continue

                latest = df.iloc[-1]
                prev = df.iloc[-2] if len(df) > 1 else latest

                data = {
                    "symbol": symbol,
                    "name": symbol.replace("USDT", ""),
                    "current_price": float(latest['close']),
                    "price_change_24h": float(latest['close'] - prev['close']),
                    "price_change_percentage_24h": float((latest['close'] - prev['close']) / prev['close'] * 100),
                    "volume_24h": float(latest['volume']),
                    "high_24h": float(df['high'].max()),
                    "low_24h": float(df['low'].min()),
                    "last_updated": latest.name
                }

                result.append(data)

            except Exception as e:
                # 单个币种失败不影响其他币种
                continue

        return response_handler.format_success(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场列表失败: {str(e)}")


@router.get("/market/overview")
async def get_market_overview():
    """
    获取市场宏观概览

    返回整个加密货币市场的宏观概览数据，包括总市值、主导率、恐惧贪婪指数等关键指标。

    ## 功能特点
    - 返回整个加密货币市场的宏观数据
    - 基于市场概览表（market_overview）的最新数据
    - 提供市场情绪和风险评估
    - 包含BTC和ETH的主导率信息
    - 无需任何参数，直接调用即可

    ## 返回数据说明
    返回的数据包括：
    - 总市值和24小时总成交量
    - 市场趋势（看涨/看跌/中性）
    - 风险等级（低/中/高）
    - BTC主导率和ETH主导率
    - 恐惧贪婪指数值和分类
    - 数据时间戳和最后更新时间

    ## 使用场景
    适用于市场总览页面、市场情绪分析、投资环境评估等场景。
    """
    try:
        # 从市场概览表获取最新数据
        overview_data = market_overview_service.get_latest_market_overview()

        if not overview_data:
            return response_handler.format_success({
                "total_market_cap": 0,
                "total_volume_24h": 0,
                "market_trend": "neutral",
                "risk_level": "medium",
                "btc_dominance": 0,
                "eth_dominance": 0,
                "fear_greed_value": 50,
                "fear_greed_classification": "Neutral",
                "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

        data = {
            "total_market_cap": overview_data.get("total_market_cap", 0),
            "total_volume_24h": overview_data.get("total_volume_24h", 0),
            "market_trend": overview_data.get("market_trend", "neutral"),
            "risk_level": overview_data.get("risk_level", "medium"),
            "btc_dominance": overview_data.get("btc_dominance", 0),
            "eth_dominance": overview_data.get("eth_dominance", 0),
            "fear_greed_value": overview_data.get("fear_greed_value", 50),
            "fear_greed_classification": overview_data.get("fear_greed_classification", "Neutral"),
            "data_timestamp": overview_data.get("data_timestamp").strftime('%Y-%m-%d %H:%M:%S') if overview_data.get("data_timestamp") else None,
            "last_updated": overview_data.get("updated_at").strftime('%Y-%m-%d %H:%M:%S') if overview_data.get("updated_at") else None
        }

        return response_handler.format_success(data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场概览失败: {str(e)}")


@router.post("/market/kline")
async def get_kline_data(
    request: KlineDataRequest
):
    """
    获取K线数据

    获取指定币种和时间框架的OHLCV（开高低收成交量）数据，适用于绘制K线图和进行技术分析。

    ## 功能特点
    - 支持 13 种时间框架（1分钟到 1月）
    - symbol 和 timeframe 为必须参数
    - 可指定精确的时间范围进行查询（start 和 end 可选）
    - 当指定 start 和 end 时，返回整个时间范围内的所有数据，忽略 limit 参数
    - 当未指定 start 和 end 时，可使用 limit 限制返回条数（默认100条）
    - 返回时间戳为毫秒级，方便前端图表展示

    ## 返回数据说明
    每条K线数据包含：
    - time: 时间戳（毫秒）
    - timestamp: 时间字符串（YYYY-MM-DD HH:MM:SS）
    - open: 开盘价
    - high: 最高价
    - low: 最低价
    - close: 收盘价
    - volume: 成交量

    ## 使用场景
    - K线图表展示
    - 技术指标计算
    - 价格走势分析
    - 量化交易策略开发
    """
    try:
        symbol = request.symbol
        timeframe = request.timeframe
        start = request.start
        end = request.end
        limit = request.limit

        # 转换时间框架格式
        timeframe_map = {
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h',
            '8h': '8h', '12h': '12h', '1d': '1d', '1w': '1w', '1M': '1M'
        }
        timeframe = timeframe_map.get(timeframe)
        if not timeframe:
            raise HTTPException(status_code=400, detail="不支持的时间间隔")

        # 处理时间范围逻辑
        effective_start = start
        effective_end = end
        effective_limit = limit

        # 如果没有指定 start 和 end，设置默认时间范围并使用 limit
        if not start and not end:
            from datetime import datetime, timedelta
            effective_end = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            effective_start = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            effective_limit = limit
        # 如果指定了 start 和 end，则忽略 limit，返回整个时间范围的数据
        elif start and end:
            effective_start = start
            effective_end = end
            effective_limit = 10000  # 设置较大的值返回所有数据

        # 获取K线数据
        df = kline_service.load_kline_data(
            symbol=symbol,
            timeframe=timeframe,
            start_time=effective_start,
            end_time=effective_end,
            limit=effective_limit
        )

        if df.empty:
            return response_handler.format_success([])

        # 转换为前端需要的格式
        kline_data = []
        for timestamp, row in df.iterrows():
            kline_data.append({
                "time": int(pd.Timestamp(timestamp).timestamp() * 1000),
                "timestamp": str(timestamp),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": float(row['volume'])
            })

        return response_handler.format_success(kline_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


@router.post("/market/indicators")
async def get_technical_indicators(
    request: TechnicalIndicatorsRequest
):
    """
    获取技术指标

    计算并返回各种技术分析指标，包括RSI、MACD、布林带、移动平均线和EMA等，帮助判断价格趋势和超买超卖状态。

    ## 功能特点
    - 基于最近200条K线数据计算指标
    - 返回5种主要技术指标
    - 提供指标信号解读和交易建议
    - 支持7种时间框架
    - v2.0新增所有指标的历史记录（带时间戳）
    - 返回最近20个历史数据点

    ## 返回格式说明
    返回的JSON包含以下字段：

    ### 基础信息
    - `symbol`: 交易对符号 (如: BTCUSDT)
    - `timeframe`: 时间框架 (如: 1h)
    - `timestamp`: 时间戳 (ISO格式)

    ### 1. RSI (相对强弱指数)
    - `rsi.value`: RSI值（0-100）
    - `rsi.signal`: 信号 (overbought/oversold/neutral)
    - `rsi.interpretation`: 指标解读
    - `rsi.history`: RSI历史数组 [{ "value": 65.50, "timestamp": "2025-11-10 10:00:00" }]

    ### 2. MACD (指数平滑异同移动平均线)
    - `macd.macd`: MACD线值
    - `macd.signal`: 信号线值
    - `macd.histogram`: 柱状图值
    - `macd.signal_type`: 信号类型 (bullish/bearish)
    - `macd.interpretation`: 信号解读
    - `macd.history`: MACD历史数组 [{ "macd": 123.45, "signal": 120.30, "histogram": 3.15, "timestamp": "..." }]

    ### 3. 布林带 (Bollinger Bands)
    - `bollinger.upper`: 上轨
    - `bollinger.middle`: 中轨(20日均线)
    - `bollinger.lower`: 下轨
    - `bollinger.position`: 价格在带中位置(0-1)
    - `bollinger.width`: 带宽
    - `bollinger.interpretation`: 位置解读
    - `bollinger.history`: 布林带历史数组 [{ "upper": 50000, "middle": 48000, "lower": 46000, "timestamp": "..." }]

    ### 4. 移动平均线 (Moving Average)
    - `ma.ma20`: 20日均线
    - `ma.ma50`: 50日均线
    - `ma.ma200`: 200日均线
    - `ma.trend`: 趋势 (uptrend/downtrend/sideways)
    - `ma.interpretation`: 趋势解读
    - `ma.history`: MA历史数组 [{ "ma20": 48200, "ma50": 47500, "ma200": 45000, "timestamp": "..." }]

    ### 5. 指数移动平均线
    - `ema.ema12`: 12日指数均线
    - `ema.ema26`: 26日指数均线
    - `ema.ema50`: 50日指数均线
    - `ema.history`: EMA历史数组 [{ "ema12": 48500, "ema26": 48000, "ema50": 47000, "timestamp": "..." }]

    ## 使用场景
    - 技术分析图表展示
    - 交易信号生成
    - 价格趋势判断
    - 超买超卖状态识别
    - 指标历史走势分析
    """
    try:
        symbol = request.symbol
        timeframe = request.timeframe

        # 设置时间范围：最近200条数据的时间范围
        from datetime import datetime, timedelta
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')

        # 获取K线数据
        df = kline_service.load_kline_data(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            limit=200
        )

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"未找到{symbol}在{timeframe}时间框架下的K线数据。请检查：1) 交易对符号是否正确（如BTCUSDT）；2) 时间框架是否有效（如1h、4h、1d）；3) 数据库中是否已同步该交易对的历史数据。建议先调用 /api/market/list 接口查看有哪些可用的交易对数据。"
            )

        # 获取最新数据
        latest = df.iloc[-1]
        close_prices = df['close'].tolist()
        high_prices = df['high'].tolist()
        low_prices = df['low'].tolist()

        # 获取时间戳（用于历史数据）
        timestamps = []
        for idx in df.index:
            if hasattr(idx, 'strftime'):
                timestamps.append(idx.strftime('%Y-%m-%d %H:%M:%S'))
            else:
                timestamps.append(str(idx))

        # 计算指标（包含历史数据）
        indicators = calculate_basic_indicators(close_prices, high_prices, low_prices, timestamps)

        # 构建返回结果（使用用户指定的格式）
        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": latest.name.strftime('%Y-%m-%dT%H:%M:%S') if hasattr(latest.name, 'strftime') else str(latest.name),

            # RSI相对强弱指数
            "rsi": {
                "value": round(indicators['rsi'], 2),
                "signal": "overbought" if indicators['rsi'] > 70 else "oversold" if indicators['rsi'] < 30 else "neutral",
                "interpretation": f"RSI为{indicators['rsi']:.2f}，{'超买' if indicators['rsi'] > 70 else '超卖' if indicators['rsi'] < 30 else '在正常范围内'}",
                "history": indicators.get('rsi_history', [])
            },

            # MACD指标
            "macd": {
                "macd": round(indicators['macd'], 2),
                "signal": round(indicators['macd_signal'], 2),
                "histogram": round(indicators['macd_hist'], 2),
                "signal_type": "bullish" if indicators['macd'] > indicators['macd_signal'] else "bearish",
                "interpretation": "MACD呈现看涨信号" if indicators['macd'] > indicators['macd_signal'] else "MACD呈现看跌信号",
                "history": indicators.get('macd_history', [])
            },

            # 布林带
            "bollinger": {
                "upper": round(indicators['bb_upper'], 2),
                "middle": round(indicators['bb_middle'], 2),
                "lower": round(indicators['bb_lower'], 2),
                "position": round((latest['close'] - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower']), 2),
                "width": round((indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle'], 2),
                "interpretation": f"价格在{'上轨附近' if latest['close'] > indicators['bb_upper'] * 0.98 else '下轨附近' if latest['close'] < indicators['bb_lower'] * 1.02 else '中轨附近'}",
                "history": indicators.get('bollinger_history', [])
            },

            # 移动平均线
            "ma": {
                "ma20": round(indicators['ma20'], 2),
                "ma50": round(indicators['ma50'], 2),
                "ma200": round(indicators['ma200'], 2),
                "trend": "uptrend" if latest['close'] > indicators['ma20'] > indicators['ma50'] else "downtrend" if latest['close'] < indicators['ma20'] < indicators['ma50'] else "sideways",
                "interpretation": "短期均线上方，趋势向上" if latest['close'] > indicators['ma20'] else "短期均线下方，趋势向下" if latest['close'] < indicators['ma20'] else "价格在均线附近震荡",
                "history": indicators.get('ma_history', [])
            },

            # 指数移动平均线（v2.0新增）
            "ema": {
                "ema12": round(indicators['ema12'], 2),
                "ema26": round(indicators['ema26'], 2),
                "ema50": round(indicators['ema50'], 2),
                "history": indicators.get('ema_history', [])
            }
        }

        return response_handler.format_success(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取技术指标失败: {str(e)}")


def calculate_basic_indicators(close_prices, high_prices, low_prices, timestamps):
    """计算基础技术指标

    Args:
        close_prices: 收盘价列表
        high_prices: 最高价列表
        low_prices: 最低价列表
        timestamps: 时间戳列表
    """
    import numpy as np

    # RSI计算
    deltas = np.diff(close_prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    # 计算RSI历史记录（带时间戳）
    rsi_history = []
    avg_gain = 0
    avg_loss = 0
    for i in range(1, len(close_prices)):
        if i == 1:
            avg_gain = gains[0] if len(gains) > 0 else 0
            avg_loss = losses[0] if len(losses) > 0 else 0
        else:
            avg_gain = (avg_gain * 13 + gains[i-1]) / 14
            avg_loss = (avg_loss * 13 + losses[i-1]) / 14

        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        # 添加时间戳
        rsi_history.append({
            "value": round(rsi, 2),
            "timestamp": timestamps[i] if i < len(timestamps) else timestamps[-1]
        })

    # 取最后14个RSI值用于当前计算
    avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else (gains[-1] if len(gains) > 0 else 0)
    avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else (losses[-1] if len(losses) > 0 else 0)

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))

    # EMA计算（指数移动平均线）
    def calculate_ema(prices, period):
        ema = [prices[0]]
        alpha = 2 / (period + 1)
        for price in prices[1:]:
            ema.append(alpha * price + (1 - alpha) * ema[-1])
        return ema

    ema12_series = calculate_ema(close_prices, 12)
    ema26_series = calculate_ema(close_prices, 26)
    ema50_series = calculate_ema(close_prices, 50)

    # MACD计算（使用标准MACD算法）
    # 1. 计算MACD线 = EMA12 - EMA26
    ema12 = ema12_series[-1]
    ema26 = ema26_series[-1]
    macd_line = ema12 - ema26

    # 2. 计算Signal线 = EMA9(MACD线)
    # 需要先计算整个MACD线的序列
    macd_line_series = [ema12_series[i] - ema26_series[i] for i in range(len(ema12_series))]

    # 计算MACD的9日EMA（信号线）
    signal_line_series = calculate_ema(macd_line_series, 9)

    # 取最新的值
    macd = macd_line_series[-1] if macd_line_series else macd_line
    macd_signal = signal_line_series[-1] if signal_line_series else macd_line

    # 3. 计算Histogram = MACD - Signal
    macd_hist = macd - macd_signal

    # MACD历史数据（带时间戳）
    macd_history = []
    for i in range(len(macd_line_series)):
        timestamp = timestamps[i+1] if i+1 < len(timestamps) else timestamps[-1]  # MACD从第2个点开始
        signal_val = signal_line_series[i] if i < len(signal_line_series) else macd_signal
        hist_val = macd_line_series[i] - signal_val
        macd_history.append({
            "macd": round(macd_line_series[i], 2),
            "signal": round(signal_val, 2),
            "histogram": round(hist_val, 2),
            "timestamp": timestamp
        })

    # 移动平均线计算（带历史记录）
    ma20_series = []
    ma50_series = []
    ma200_series = []

    for i in range(len(close_prices)):
        # MA20
        if i >= 19:
            ma20_val = np.mean(close_prices[i-19:i+1])
        else:
            ma20_val = np.mean(close_prices[:i+1])
        ma20_series.append(ma20_val)

        # MA50
        if i >= 49:
            ma50_val = np.mean(close_prices[i-49:i+1])
        else:
            ma50_val = np.mean(close_prices[:i+1])
        ma50_series.append(ma50_val)

        # MA200
        if i >= 199:
            ma200_val = np.mean(close_prices[i-199:i+1])
        else:
            ma200_val = np.mean(close_prices[:i+1])
        ma200_series.append(ma200_val)

    ma20 = ma20_series[-1]
    ma50 = ma50_series[-1]
    ma200 = ma200_series[-1]

    # MA历史数据（带时间戳）
    ma_history = []
    for i in range(len(close_prices)):
        timestamp = timestamps[i]
        ma_history.append({
            "ma20": round(ma20_series[i], 2),
            "ma50": round(ma50_series[i], 2),
            "ma200": round(ma200_series[i], 2),
            "timestamp": timestamp
        })

    # 布林带计算（带历史记录）
    bb_upper_series = []
    bb_middle_series = []
    bb_lower_series = []

    for i in range(len(close_prices)):
        # 计算20日标准差
        if i >= 19:
            prices_for_std = close_prices[i-19:i+1]
            std_val = np.std(prices_for_std)
            ma_val = ma20_series[i]
        else:
            prices_for_std = close_prices[:i+1]
            std_val = np.std(prices_for_std)
            ma_val = np.mean(prices_for_std)

        bb_middle_val = ma_val
        bb_upper_val = bb_middle_val + (std_val * 2)
        bb_lower_val = bb_middle_val - (std_val * 2)

        bb_middle_series.append(bb_middle_val)
        bb_upper_series.append(bb_upper_val)
        bb_lower_series.append(bb_lower_val)

    bb_middle = bb_middle_series[-1]
    bb_upper = bb_upper_series[-1]
    bb_lower = bb_lower_series[-1]

    # 布林带历史数据（带时间戳）
    bollinger_history = []
    for i in range(len(close_prices)):
        timestamp = timestamps[i]
        bollinger_history.append({
            "upper": round(bb_upper_series[i], 2),
            "middle": round(bb_middle_series[i], 2),
            "lower": round(bb_lower_series[i], 2),
            "timestamp": timestamp
        })

    # EMA历史数据（带时间戳）
    ema_history = []
    for i in range(len(close_prices)):
        timestamp = timestamps[i]
        ema_history.append({
            "ema12": round(ema12_series[i], 2),
            "ema26": round(ema26_series[i], 2),
            "ema50": round(ema50_series[i], 2),
            "timestamp": timestamp
        })

    return {
        'rsi': rsi,
        'rsi_history': rsi_history[-20:] if len(rsi_history) > 20 else rsi_history,  # 返回最近20个RSI值（带时间戳）
        'macd': macd,
        'macd_signal': macd_signal,
        'macd_hist': macd_hist,
        'macd_history': macd_history[-20:] if len(macd_history) > 20 else macd_history,  # 返回最近20个MACD值（带时间戳）
        'ma20': ma20,
        'ma50': ma50,
        'ma200': ma200,
        'ma_history': ma_history[-20:] if len(ma_history) > 20 else ma_history,  # 返回最近20个MA值（带时间戳）
        'ema12': ema12_series[-1],
        'ema26': ema26_series[-1],
        'ema50': ema50_series[-1],
        'ema_history': ema_history[-20:] if len(ema_history) > 20 else ema_history,  # 返回最近20个EMA值（带时间戳）
        'bb_upper': bb_upper,
        'bb_middle': bb_middle,
        'bb_lower': bb_lower,
        'bollinger_history': bollinger_history[-20:] if len(bollinger_history) > 20 else bollinger_history  # 返回最近20个布林带值（带时间戳）
    }


@router.post("/market/trend")
async def get_trend_data(
    request: TrendDataRequest
):
    """
    获取趋势数据

    返回价格趋势分析数据，支持多币种对比和多个时间周期
    提供趋势方向、强度、变化百分比和波动率分析
    """
    try:
        symbol = request.symbol
        period = request.period

        # 获取对应时间框架的数据
        from datetime import datetime, timedelta
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if period == '1d':
            start_time = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
            timeframe = '1h'
        elif period == '7d':
            start_time = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
            timeframe = '4h'
        else:  # 30d
            start_time = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
            timeframe = '1d'

        df = kline_service.load_kline_data(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            limit=100
        )

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"未找到{symbol}在{timeframe}时间框架下的K线数据（用于{period}趋势分析）。请检查交易对是否正确，时间框架是否有效，数据库中是否有该交易对的历史数据。"
            )

        # 计算趋势
        latest = df.iloc[-1]
        first = df.iloc[0]
        change_pct = (latest['close'] - first['close']) / first['close'] * 100

        # 计算波动率
        returns = df['close'].pct_change().dropna()
        volatility = returns.std()

        result = {
            "period": period,
            "symbol": symbol,
            "trend_analysis": {
                "direction": "upward" if change_pct > 0 else "downward",
                "strength": min(abs(change_pct) / 10, 1.0),
                "change_percentage": change_pct,
                "interpretation": f"价格{'上升' if change_pct > 0 else '下降'}了{abs(change_pct):.2f}%"
            },
            "volatility": {
                "value": volatility,
                "level": "high" if volatility > 0.05 else "medium" if volatility > 0.02 else "low",
                "interpretation": f"波动率{'高' if volatility > 0.05 else '中等' if volatility > 0.02 else '低'}"
            },
            "price_points": [
                {
                    "timestamp": str(idx),
                    "price": float(row['close']),
                    "date": str(idx)[:10]
                }
                for idx, row in df.tail(30).iterrows()
            ],
            "last_updated": str(latest.name)
        }

        return response_handler.format_success(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取趋势数据失败: {str(e)}")


@router.post("/market/crypto-futures")
async def get_crypto_futures(
    request: CryptoFuturesRequest
):
    """
    获取期货市场数据

    返回永续合约的持仓量、资金费率、多空比例等期货特有指标
    提供期货市场情绪和资金流向分析

    ⚠️ 此功能暂不可用：请接入Binance期货API获取真实数据
    """
    raise HTTPException(
        status_code=503,
        detail="期货数据功能暂不可用，请先配置Binance期货API密钥"
    )


@router.post("/market/rank")
async def get_market_rank(
    request: MarketRankRequest
):
    """
    获取市场排行

    按交易量排序的加密货币排行榜
    提供市场热门币种排名、价格、涨跌幅、交易量和市值信息
    """
    try:
        limit = request.limit

        # 设置时间范围：最近24小时
        from datetime import datetime, timedelta
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')

        # 默认返回BTCUSDT排行
        df = kline_service.load_kline_data(
            symbol="BTCUSDT",
            timeframe="1h",
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        if df.empty:
            return response_handler.format_success([])

        rank_data = []
        for i, (timestamp, row) in enumerate(df.iterrows(), 1):
            rank_data.append({
                "rank": i,
                "symbol": "BTCUSDT",
                "name": "Bitcoin",
                "current_price": float(row['close']),
                "price_change_percentage_24h": 0.0,  # 简化
                "volume_24h": float(row['volume']),
                "market_cap": float(row['close']) * 19750000,
                "circulating_supply": 19750000.0
            })

        return response_handler.format_success(rank_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取市场排行失败: {str(e)}")


@router.post("/market/support-resistance")
async def get_support_resistance(
    request: SupportResistanceRequest
):
    """
    获取支撑阻力位

    分析价格图表，识别关键支撑位和阻力位，用于交易决策参考。

    ## 功能特点
    - 基于价格走势分析识别关键价位
    - 计算支撑/阻力位的强度和触及次数
    - 支持多个时间框架分析
    - 返回当前价格与关键位置的关系

    ## 返回数据说明
    返回的数据包括：
    - 交易对符号和时间框架
    - 支撑位数组（support_levels）
      - price: 支撑位价格
      - strength: 强度系数（0-1），数值越高表示该位置越重要
      - touches: 价格触及该位置的次数
      - type: 级别类型（support）
    - 阻力位数组（resistance_levels）
      - price: 阻力位价格
      - strength: 强度系数（0-1）
      - touches: 价格触及该位置的次数
      - type: 级别类型（resistance）
    - 当前价格（current_price）
    - 最后更新时间

    ## 使用场景
    - 交易入场点分析
    - 止损止盈位设置
    - 价格突破策略
    - 风险控制参考
    """
    try:
        symbol = request.symbol
        timeframe = request.timeframe

        # 设置时间范围：获取足够的历史数据进行分析
        from datetime import datetime, timedelta
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 根据时间框架设置分析范围
        if timeframe == '1h':
            start_time = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        elif timeframe == '4h':
            start_time = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d %H:%M:%S')
        elif timeframe == '1d':
            start_time = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d %H:%M:%S')
        else:  # 1w
            start_time = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')

        # 获取K线数据
        df = kline_service.load_kline_data(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )

        if df.empty:
            return response_handler.format_success({
                "symbol": symbol,
                "timeframe": timeframe,
                "support_levels": [],
                "resistance_levels": [],
                "current_price": 0.0,
                "last_updated": end_time
            })

        # 简化版支撑阻力位计算
        # 实际项目中应使用更复杂的算法（如斐波那契、趋势线等）
        high_prices = df['high'].values
        low_prices = df['low'].values
        close_prices = df['close'].values
        current_price = float(close_prices[-1])

        # 查找局部高点和低点
        support_levels = []
        resistance_levels = []

        # 简单的支撑阻力位识别：基于价格密集区
        # 将价格分为10个区间，统计每个区间的触达次数
        price_range = high_prices.max() - low_prices.min()
        bucket_size = price_range / 10

        buckets = {i: 0 for i in range(10)}
        for high, low in zip(high_prices, low_prices):
            for i in range(10):
                bucket_start = low_prices.min() + i * bucket_size
                bucket_end = bucket_start + bucket_size
                # 优化：判断K线是否穿过价格区间（而非完全覆盖）
                # 条件：K线高价 > 区间起点 AND K线低价 < 区间终点
                if high > bucket_start and low < bucket_end:
                    buckets[i] += 1

        # 选择触达次数最多的价位作为支撑/阻力位
        sorted_buckets = sorted(buckets.items(), key=lambda x: x[1], reverse=True)

        for bucket_idx, touches in sorted_buckets[:3]:  # 取前3个
            price_level = low_prices.min() + bucket_idx * bucket_size + bucket_size / 2
            if price_level < current_price:
                support_levels.append({
                    "price": round(price_level, 2),
                    "strength": round(min(touches / 10.0, 1.0), 2),
                    "touches": touches,
                    "type": "support"
                })
            else:
                resistance_levels.append({
                    "price": round(price_level, 2),
                    "strength": round(min(touches / 10.0, 1.0), 2),
                    "touches": touches,
                    "type": "resistance"
                })

        # 确保至少有基础数据
        if not support_levels:
            # 使用最近的低点作为支撑
            min_idx = df['low'].idxmin()
            support_levels.append({
                "price": round(float(df.loc[min_idx, 'low']), 2),
                "strength": 0.5,
                "touches": 1,
                "type": "support"
            })

        if not resistance_levels:
            # 使用最近的高点作为阻力
            max_idx = df['high'].idxmax()
            resistance_levels.append({
                "price": round(float(df.loc[max_idx, 'high']), 2),
                "strength": 0.5,
                "touches": 1,
                "type": "resistance"
            })

        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "support_levels": support_levels[:5],  # 最多返回5个
            "resistance_levels": resistance_levels[:5],  # 最多返回5个
            "current_price": current_price,
            "last_updated": str(df.index[-1])
        }

        return response_handler.format_success(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取支撑阻力位失败: {str(e)}")


@router.post("/market/crypto-indicators")
async def get_crypto_indicators(
    request: CryptoIndicatorsRequest
):
    """
    获取币圈原生技术指标

    计算并返回币圈特有的技术指标，包括Supertrend、Heikin-Ashi、PSAR、VWAP、StochRSI、VW-MACD和EMA Ribbon等。
    这些指标专为加密货币市场优化，比传统指标更适合币圈的高波动性和高杠杆特性。

    ## 功能特点
    - 支持7种币圈原生指标
    - 专为币圈优化的参数设置
    - 返回实时计算结果和历史数据
    - 支持多种时间框架

    ## 指标说明

    ### 1. Supertrend（超级趋势）
    - 基于ATR的动态止损指标
    - 1h周期推荐：ATR 10 × 2.0
    - 4h周期推荐：ATR 10 × 3.0
    - 用于判断趋势方向和设置止损

    ### 2. Heikin-Ashi（平均K线）
    - 平滑价格K线，过滤市场噪音
    - 建议配合成交量分析真实趋势
    - 不建议单独使用，需结合其他指标

    ### 3. PSAR（抛物线转向指标）
    - 币圈优化参数：af_start=0.008, af_max=0.08
    - 传统参数：af_start=0.02, af_max=0.2
    - 用于识别趋势转换点

    ### 4. VWAP（成交量加权平均价）
    - 机构级"日内公平价"
    - 日线重置，价格>+2σ视为高价区
    - 价格<-2σ视为低价区

    ### 5. StochRSI（随机RSI）
    - 比裸RSI早1根K线出信号
    - 参数：9,3,3，阈值20/80
    - 用于超买超卖判断

    ### 6. VW-MACD（成交量加权MACD）
    - 参数：8,21,5
    - 考虑成交量因素的MACD变种
    - 更能反映资金流向

    ### 7. EMA Ribbon（指数均线带）
    - 6条EMA线：8/13/21/34/55/89
    - 多头排列：看涨信号
    - 空头排列：看跌信号

    ## 返回格式
    返回JSON包含所选指标的最新值、历史数据和信号解读。
    """
    try:
        symbol = request.symbol
        timeframe = request.timeframe
        indicator_type = request.indicator_type

        # 设置时间范围：获取足够的历史数据
        from datetime import datetime, timedelta
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')

        # 获取K线数据
        df = kline_service.load_kline_data(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            limit=200
        )

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"未找到{symbol}在{timeframe}时间框架下的K线数据"
            )

        # 转换为numpy数组
        open_price = df['open'].values
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        volume = df['volume'].values

        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": str(df.index[-1]),
            "indicators": {}
        }

        # 根据请求类型计算指标
        if indicator_type in ["supertrend", "all"]:
            st_result = CryptoIndicators.calculate_supertrend(high, low, close, 10, 2.0 if timeframe == "1h" else 3.0)
            result["indicators"]["supertrend"] = {
                "value": float(st_result['supertrend'][-1]),
                "direction": "bullish" if st_result['direction'][-1] == 1 else "bearish",
                "atr": float(st_result['atr'][-1]),
                "upper_band": float(st_result['upper_band'][-1]),
                "lower_band": float(st_result['lower_band'][-1]),
                "interpretation": f"Supertrend显示{'看涨' if st_result['direction'][-1] == 1 else '看跌'}趋势"
            }

        if indicator_type in ["heikin_ashi", "all"]:
            ha_result = CryptoIndicators.calculate_heikin_ashi(open_price, high, low, close, volume)
            result["indicators"]["heikin_ashi"] = {
                "ha_open": float(ha_result['ha_open'][-1]),
                "ha_high": float(ha_result['ha_high'][-1]),
                "ha_low": float(ha_result['ha_low'][-1]),
                "ha_close": float(ha_result['ha_close'][-1]),
                "trend": "bullish" if ha_result['ha_close'][-1] > ha_result['ha_open'][-1] else "bearish",
                "interpretation": f"Heikin-Ashi显示{'看涨' if ha_result['ha_close'][-1] > ha_result['ha_open'][-1] else '看跌'}趋势"
            }

        if indicator_type in ["psar", "all"]:
            psar_result = CryptoIndicators.calculate_psar(high, low, close)
            result["indicators"]["psar"] = {
                "value": float(psar_result['psar'][-1]),
                "direction": "bullish" if psar_result['trend'][-1] == 1 else "bearish",
                "ep": float(psar_result['ep'][-1]),
                "af": float(psar_result['af'][-1]),
                "interpretation": f"PSAR显示{'看涨' if psar_result['trend'][-1] == 1 else '看跌'}趋势"
            }

        if indicator_type in ["vwap", "all"]:
            vwap_result = CryptoIndicators.calculate_vwap(high, low, close, volume)
            result["indicators"]["vwap"] = {
                "value": float(vwap_result['vwap'][-1]),
                "upper_band": float(vwap_result['upper_band'][-1]),
                "lower_band": float(vwap_result['lower_band'][-1]),
                "position": "above" if close[-1] > vwap_result['vwap'][-1] else "below",
                "interpretation": f"价格{'高于' if close[-1] > vwap_result['vwap'][-1] else '低于'}VWAP"
            }

        if indicator_type in ["stoch_rsi", "all"]:
            srsi_result = CryptoIndicators.calculate_stoch_rsi(close)
            result["indicators"]["stoch_rsi"] = {
                "stoch_rsi": float(srsi_result['stoch_rsi'][-1]),
                "k_line": float(srsi_result['k_line'][-1]),
                "d_line": float(srsi_result['d_line'][-1]),
                "signal": srsi_result['signal'][-1] if len(srsi_result['signal']) > 0 else "neutral",
                "interpretation": f"StochRSI为{srsi_result['k_line'][-1]:.2f}，{srsi_result['signal'][-1] if len(srsi_result['signal']) > 0 else 'neutral'}"
            }

        if indicator_type in ["vw_macd", "all"]:
            vw_macd_result = CryptoIndicators.calculate_vw_macd(close, volume)
            result["indicators"]["vw_macd"] = {
                "vw_macd": float(vw_macd_result['vw_macd'][-1]),
                "signal": float(vw_macd_result['signal'][-1]),
                "histogram": float(vw_macd_result['histogram'][-1]),
                "interpretation": "VW-MACD看涨" if vw_macd_result['vw_macd'][-1] > vw_macd_result['signal'][-1] else "VW-MACD看跌"
            }

        if indicator_type in ["ema_ribbon", "all"]:
            ema_result = CryptoIndicators.calculate_ema_ribbon(close)
            result["indicators"]["ema_ribbon"] = {
                "ema8": float(ema_result['ema8'][-1]),
                "ema13": float(ema_result['ema13'][-1]),
                "ema21": float(ema_result['ema21'][-1]),
                "ema34": float(ema_result['ema34'][-1]),
                "ema55": float(ema_result['ema55'][-1]),
                "ema89": float(ema_result['ema89'][-1]),
                "trend": "bullish" if ema_result['ribbon_trend'][-1] == 1 else "bearish" if ema_result['ribbon_trend'][-1] == -1 else "neutral",
                "interpretation": f"EMA Ribbon显示{'多头排列' if ema_result['ribbon_trend'][-1] == 1 else '空头排列' if ema_result['ribbon_trend'][-1] == -1 else '震荡'}"
            }

        return response_handler.format_success(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取币圈原生指标失败: {str(e)}")


@router.post("/market/short-template")
async def get_short_template(
    request: ShortTemplateRequest
):
    """
    获取币圈短打模板策略信号

    基于币圈优化的短打模板策略，综合分析多个技术指标信号。
    适合1小时和4小时时间框架的短线交易。

    ## 策略逻辑（满足4中3即可执行）

    ### 做多信号：
    ① EMA Ribbon多头排列 + Supertrend多头
    ② StochRSI金叉出超卖区
    ③ 交易所净流入负值（提币）
    ④ Funding负值或低于-0.05%

    ### 做空信号（反向）

    ## 主图指标
    - Heikin-Ashi蜡烛（趋势过滤）
    - EMA Ribbon 8/13/21/34/55/89（多空排列）
    - Supertrend (ATR 10, 乘2.0)（动态止损）
    - 日线VWAP（机构基准）

    ## 副图指标
    - StochRSI 9,3,3, 20/80（比裸RSI早1根K）
    - VW-MACD 8,21,5（成交量加权）
    - 永续Funding Rate（Binance）

    ## 止损策略
    - 使用Supertrend作为动态止损
    - 或使用ATR(14)×1.5作为固定止损

    ## 返回数据
    返回详细的信号分析、交易建议、风险提示和指标状态。
    """
    try:
        symbol = request.symbol
        timeframe = request.timeframe

        # 设置时间范围
        from datetime import datetime, timedelta
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        start_time = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')

        # 获取K线数据
        df = kline_service.load_kline_data(
            symbol=symbol,
            timeframe=timeframe,
            start_time=start_time,
            end_time=end_time,
            limit=100
        )

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"未找到{symbol}在{timeframe}时间框架下的K线数据"
            )

        # 转换为numpy数组
        open_price = df['open'].values
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        volume = df['volume'].values

        # 执行短打模板分析
        template_result = CryptoIndicators.analyze_short_template(
            open_price, high, low, close, volume
        )

        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": str(df.index[-1]),
            "strategy_name": "Crypto Short Template v1.0",
            "signals": {
                "ema_ribbon_bullish": template_result['signals']['ema_ribbon_bullish'],
                "supertrend_bullish": template_result['signals']['supertrend_bullish'],
                "stoch_rsi_bullish": template_result['signals']['stoch_rsi_bullish'],
                "netflow_bullish": template_result['signals']['netflow_bullish'],
                "funding_bullish": template_result['signals']['funding_bullish']
            },
            "signal_count": {
                "bullish": template_result['bullish_count'],
                "bearish": template_result['bearish_count']
            },
            "recommendation": template_result['recommendation'],
            "risk_level": "high" if abs(template_result['bullish_count'] - template_result['bearish_count']) <= 1 else "medium",
            "indicators": {
                "supertrend": template_result['supertrend'],
                "stoch_rsi": template_result['stoch_rsi'],
                "ema_ribbon_trend": template_result['ema_ribbon_trend']
            },
            "trading_logic": {
                "long_conditions": [
                    "EMA Ribbon多头排列",
                    "Supertrend显示上涨",
                    "StochRSI从超卖区金叉",
                    "交易所净流入为负（提币）",
                    "Funding费率为负"
                ],
                "required_signals": 3,
                "stop_loss": "Supertrend或ATR(14)×1.5"
            },
            "interpretation": f"当前{template_result['bullish_count']}个看涨信号，{template_result['bearish_count']}个看跌信号，建议：{template_result['recommendation']}"
        }

        return response_handler.format_success(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取短打模板信号失败: {str(e)}")


@router.post("/market/futures-data")
async def get_futures_data(
    request: FuturesDataRequest
):
    """
    获取期货市场数据

    返回永续合约的资金费率、未平仓量、多空比例等期货特有指标。
    提供期货市场情绪和资金流向分析。

    ⚠️ 此功能暂不可用：请接入Binance期货API获取真实数据
    """
    raise HTTPException(
        status_code=503,
        detail="期货市场数据功能暂不可用，请先配置Binance期货API密钥"
    )


@router.post("/market/onchain-data")
async def get_onchain_data(
    request: OnChainDataRequest
):
    """
    获取链上情绪指标

    返回交易所净流入、aSOPR、杠杆比率等链上情绪指标。
    这些指标基于区块链数据，反映市场深层次的情绪变化。

    ⚠️ 此功能暂不可用：请接入Glassnode/CryptoQuant API获取真实数据
    """
    raise HTTPException(
        status_code=503,
        detail="链上数据功能暂不可用，请先配置Glassnode/CryptoQuant API"
    )
