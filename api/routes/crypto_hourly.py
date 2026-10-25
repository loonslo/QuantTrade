# -*- coding: utf-8 -*-
"""
加密货币小时K线数据API路由
提供加密货币1H/4H K线数据的API接口
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from services.orm.crypto_hourly_kline_orm import get_crypto_hourly_kline_orm
from services.data_sync.tasks.crypto_hourly_sync import get_crypto_hourly_sync_service
from utils.core.logger_manager import get_logger

router = APIRouter(prefix="/crypto/hourly", tags=["加密货币小时K线"])


@router.get("/klines/{symbol}", summary="获取加密货币小时K线")
async def get_crypto_hourly_klines(
    symbol: str,
    interval: str = Query("1h", description="时间周期 (1h/4h)"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD HH:MM:SS"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD HH:MM:SS")
):
    """
    获取加密货币指定日期范围的小时K线数据
    
    - **symbol**: 交易对，如 BTC/USDT, ETH/USDT
    - **interval**: 时间周期，支持 '1h' 和 '4h'
    - **start_date**: 开始日期，格式 YYYY-MM-DD HH:MM:SS
    - **end_date**: 结束日期，格式 YYYY-MM-DD HH:MM:SS
    """
    try:
        orm = get_crypto_hourly_kline_orm()
        
        # 设置默认日期范围（最近7天）
        if not start_date:
            from datetime import timedelta
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        klines = orm.get_klines(symbol.upper(), start_date, end_date, interval)
        
        return {
            "success": True,
            "data": klines,
            "count": len(klines),
            "symbol": symbol.upper(),
            "interval": interval,
            "date_range": {"start": start_date, "end": end_date},
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"获取 {symbol} K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest/{symbol}", summary="获取加密货币最新小时K线")
async def get_crypto_hourly_latest(
    symbol: str,
    interval: str = Query("1h", description="时间周期 (1h/4h)")
):
    """
    获取加密货币的最新小时K线数据
    
    - **symbol**: 交易对，如 BTC/USDT, ETH/USDT
    - **interval**: 时间周期，支持 '1h' 和 '4h'
    """
    try:
        orm = get_crypto_hourly_kline_orm()
        latest = orm.get_latest(symbol.upper(), interval)
        
        if not latest:
            raise HTTPException(status_code=404, detail=f"未找到 {symbol} 的数据，请先同步")
        
        return {
            "success": True,
            "data": latest,
            "timestamp": datetime.now()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 {symbol} 最新K线失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync", summary="同步加密货币小时K线数据")
async def sync_crypto_hourly_klines(
    symbols: str = Query(None, description="币种列表，逗号分隔，默认同步全部"),
    intervals: str = Query("1h,4h", description="周期列表，逗号分隔"),
    limit: int = Query(500, description="每次同步获取的条数", ge=100, le=1000)
):
    """
    手动触发加密货币小时K线数据同步
    
    - **symbols**: 币种列表，如 'BTC/USDT,ETH/USDT'，空表示全部
    - **intervals**: 周期列表，如 '1h,4h'
    - **limit**: 每次同步获取的条数，默认500条
    """
    try:
        sync_service = get_crypto_hourly_sync_service()
        
        # 解析币种列表
        symbol_list = None
        if symbols:
            symbol_list = [s.strip() for s in symbols.split(',')]
        
        # 解析周期列表
        interval_list = [i.strip() for i in intervals.split(',')]
        
        results = await sync_service.sync_all(
            symbols=symbol_list,
            intervals=interval_list,
            limit=limit
        )
        
        success_count = sum(1 for v in results.values() if v)
        fail_count = len(results) - success_count
        
        return {
            "success": fail_count == 0,
            "message": f"同步完成: 成功 {success_count}, 失败 {fail_count}",
            "results": results,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"同步加密货币小时K线失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", summary="获取加密货币小时K线同步状态")
async def get_crypto_hourly_status():
    """
    获取所有加密货币小时K线的同步状态
    """
    try:
        sync_service = get_crypto_hourly_sync_service()
        status = sync_service.get_sync_status()
        
        return {
            "success": True,
            "data": status,
            "count": len(status),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"获取同步状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
