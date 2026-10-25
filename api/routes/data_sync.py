#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据同步API（精简）
"""

from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from api.schemas.data_sync import TechnicalIndicatorRecord

from utils.api.responses import (
    create_success_response,
    create_error_response,
)

# 路由器
router = APIRouter(prefix="/data-sync", tags=["数据同步"])


@router.post("/kline/manual-sync")
async def manual_sync_kline(request: Request, timeframes: Optional[str] = None, symbols: Optional[str] = None,
                            limit: Optional[int] = None) -> JSONResponse:
    """手动触发K线多时间框架同步。

    Query:
    - timeframes: 逗号分隔的时间框架列表，如 "1m,1h,1d"；为空或为 "all" 表示全部支持的时间框架
    - symbols: 逗号分隔的交易对列表，如 "BTCUSDT,ETHUSDT"；为空使用默认
    - limit: 每个时间框架拉取条数；为空使用默认配置
    """
    try:
        from services.data_sync.tasks.kline_data_sync import get_kline_data_sync_service

        svc = get_kline_data_sync_service()
        supported = set(svc.get_supported_timeframes())

        # 解析 timeframes
        parsed_timeframes: Optional[List[str]] = None
        if timeframes is not None:
            tf_str = timeframes.strip()
            if tf_str and tf_str.lower() != "all":
                parsed_timeframes = [t.strip() for t in tf_str.split(",") if t.strip()]

        # 解析 symbols
        parsed_symbols: Optional[List[str]] = None
        if symbols is not None:
            sym_str = symbols.strip()
            if sym_str:
                parsed_symbols = [s.strip() for s in sym_str.split(",") if s.strip()]

        # 校验 limit（若提供）
        if limit is not None and limit <= 0:
            return create_error_response(
                error_code="INVALID_LIMIT",
                message=f"数据条数必须大于0: {limit}",
                status_code=400,
                request=request,
            )

        # 未提供时间框架 => 全部同步
        if not parsed_timeframes:
            ok = await svc.manual_sync_all_timeframes_kline_data(symbols=parsed_symbols, limit=limit or 100)
            data = {
                "mode": "all_timeframes",
                "supported_timeframes": sorted(list(supported)),
                "success": bool(ok),
            }
            return create_success_response(data=data, message="已触发全部时间框架K线手动同步", request=request)

        # 校验指定时间框架
        invalid = [tf for tf in parsed_timeframes if tf not in supported]
        if invalid:
            return create_error_response(
                error_code="INVALID_TIMEFRAME",
                message=f"不支持的时间框架: {invalid}; 支持: {sorted(supported)}",
                status_code=400,
                request=request,
            )

        results: Dict[str, bool] = {}
        for tf in parsed_timeframes:
            ok = await svc.manual_sync_kline_data(timeframe=tf, symbols=parsed_symbols, limit=limit or 100)
            results[tf] = bool(ok)

        overall = any(results.values()) if results else False
        data = {
            "mode": "partial_timeframes",
            "timeframes": parsed_timeframes,
            "results": results,
            "success": overall,
        }
        return create_success_response(data=data, message="已触发指定时间框架K线手动同步", request=request)

    except Exception as e:
        return create_error_response(
            error_code="MANUAL_KLINE_SYNC_ERROR",
            message=f"手动K线同步触发失败: {e}",
            status_code=500,
            request=request,
        )


@router.post("/market-overview/manual-sync")
async def manual_sync_market_overview(request: Request) -> JSONResponse:
    """手动触发市场概览同步。"""
    try:
        from services.data_sync.tasks.market_overview import get_market_overview_sync_task

        task = get_market_overview_sync_task()
        result = await task.execute()

        # 将枚举状态转换为字符串，避免JSON序列化错误
        status_value = None
        if hasattr(result, "status") and result.status is not None:
            status_value = getattr(result.status, "name", str(result.status))

        data: Dict[str, Optional[str]] = {
            "task_id": "market_overview_sync",
            "status": status_value,
            "error_message": getattr(result, "error_message", None),
        }
        return create_success_response(data=data, message="已触发市场概览手动同步", request=request)
    except Exception as e:
        return create_error_response(
            error_code="MANUAL_MARKET_OVERVIEW_SYNC_ERROR",
            message=f"手动市场概览同步触发失败: {e}",
            status_code=500,
            request=request,
        )


@router.post("/market-rank/manual-sync")
async def manual_sync_market_rank(
        request: Request,
        quote_assets: Optional[str] = None,
        limit: Optional[int] = None,
) -> JSONResponse:
    """手动触发市场排行（Market Rank）同步。

    Query:
    - quote_assets: 逗号分隔的计价货币列表，如 "USDT,BTC,ETH"；为空使用任务默认
    - limit: 每个计价货币取前N名；为空使用任务默认
    """
    try:
        from services.data_sync.tasks.crypto_market_rank_sync import get_crypto_market_rankings_sync_task

        task = get_crypto_market_rankings_sync_task()

        # 动态覆盖任务默认参数（不改任务文件，满足手动参数化需求）
        if quote_assets is not None:
            qa = [q.strip() for q in quote_assets.split(",") if q.strip()]
            if qa:
                setattr(task, 'default_quote_assets', qa)
        if limit is not None:
            if limit <= 0:
                return create_error_response(
                    error_code="INVALID_LIMIT",
                    message=f"数据条数必须大于0: {limit}",
                    status_code=400,
                    request=request,
                )
            setattr(task, 'default_limit', limit)

        result = await task.execute()

        status_value = None
        if hasattr(result, "status") and result.status is not None:
            status_value = getattr(result.status, "name", str(result.status))

        data: Dict[str, Any] = {
            "task_id": "crypto_market_rankings_sync",
            "status": status_value,
            "error_message": getattr(result, "error_message", None),
            "quote_assets": getattr(task, 'default_quote_assets', None),
            "limit": getattr(task, 'default_limit', None),
        }
        return create_success_response(data=data, message="已触发市场排行手动同步", request=request)
    except Exception as e:
        return create_error_response(
            error_code="MANUAL_MARKET_RANK_SYNC_ERROR",
            message=f"手动市场排行同步触发失败: {e}",
            status_code=500,
            request=request,
        )


@router.post("/futures/manual-sync")
async def manual_sync_futures(request: Request, symbols: Optional[str] = None) -> JSONResponse:
    """手动触发期货数据同步

    Query:
    - symbols: 逗号分隔的交易对列表，如 "BTCUSDT,ETHUSDT"；为空使用默认列表
    """
    try:
        from services.data_sync.tasks.futures_data_sync_v2 import get_futures_data_sync_service_v2

        svc = get_futures_data_sync_service_v2()

        # 解析 symbols
        parsed_symbols: Optional[List[str]] = None
        if symbols is not None:
            sym_str = symbols.strip()
            if sym_str:
                parsed_symbols = [s.strip() for s in sym_str.split(",") if s.strip()]

        # 手动同步（存储趋势数据）
        success = await svc.sync_futures_data(symbols=parsed_symbols, auto_sync=False)

        data = {
            "mode": "manual_sync",
            "requested_symbols": parsed_symbols,
            "supported_symbols": svc.SYNC_CONFIG.get('symbols', []),
            "success": success,
            "description": "手动期货数据同步（包含趋势数据）"
        }

        message = "已触发期货数据手动同步"
        if parsed_symbols:
            message += f"，交易对: {parsed_symbols}"

        return create_success_response(data=data, message=message, request=request)

    except Exception as e:
        return create_error_response(
            error_code="MANUAL_FUTURES_SYNC_ERROR",
            message=f"手动期货同步触发失败: {e}",
            status_code=500,
            request=request,
        )


@router.post("/technical-indicators/manual-sync")
async def manual_sync_technical_indicators(
        request: Request,
        timeframe: str,
        symbol: str,
) -> JSONResponse:
    try:
        from services.data_sync.tasks.indicators_sync import get_technical_indicators_sync_service

        svc = get_technical_indicators_sync_service()

        # 基于K线数据计算并写入
        ok = await svc.compute_and_upsert_indicators(timeframe=timeframe, symbol=symbol, lookback=500)

        data = {
            "timeframe": timeframe,
            "symbol": symbol,
            "record_count": 0,  # 计算方法内部会记录真实数量到日志
            "success": bool(ok),
        }
        return create_success_response(data=data, message="已触发技术指标手动同步（基于K线计算）", request=request)
    except Exception as e:
        return create_error_response(
            error_code="MANUAL_TECHNICAL_INDICATORS_SYNC_ERROR",
            message=f"手动技术指标同步触发失败: {e}",
            status_code=500,
            request=request,
        )
