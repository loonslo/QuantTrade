# -*- coding: utf-8 -*-
"""
美股基本面数据API路由
提供美股基本面数据的API接口
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from services.orm.us_stocks_fundamental_orm import get_us_stock_fundamental_orm
from services.data_sync.tasks.us_fundamental_sync import get_us_fundamental_sync_service
from utils.core.logger_manager import get_logger

logger = get_logger("us_fundamental_api")
router = APIRouter(prefix="/us-market/us-stocks", tags=["美股基本面数据"])


@router.get("/fundamental/{symbol}", summary="获取美股基本面数据")
async def get_us_stock_fundamental(symbol: str):
    """
    获取单只美股的基本面数据
    
    - **symbol**: 股票代码，如 AAPL, MSFT, GOOGL
    """
    try:
        orm = get_us_stock_fundamental_orm()
        latest = orm.get_latest(symbol.upper())
        
        if not latest:
            raise HTTPException(status_code=404, detail=f"未找到 {symbol} 的基本面数据，请先同步")
        
        return {
            "success": True,
            "data": latest,
            "timestamp": datetime.now()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 {symbol} 基本面数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/screener", summary="基本面筛选器")
async def get_us_stock_screener(
    pe_max: Optional[float] = Query(None, description="市盈率上限"),
    roe_min: Optional[float] = Query(None, description="净资产收益率下限"),
    sector: Optional[str] = Query(None, description="行业（暂不支持）")
):
    """
    按基本面条件筛选美股
    
    - **pe_max**: 市盈率上限，如 30
    - **roe_min**: 净资产收益率下限，如 0.1 (表示10%)
    - **sector**: 行业（暂不支持精确筛选）
    """
    try:
        orm = get_us_stock_fundamental_orm()
        results = orm.get_by_criteria(pe_max=pe_max, roe_min=roe_min, sector=sector)
        
        return {
            "success": True,
            "data": results,
            "count": len(results),
            "filters": {
                "pe_max": pe_max,
                "roe_min": roe_min,
                "sector": sector
            },
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"筛选美股失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings-calendar", summary="获取财报日历")
async def get_earnings_calendar(
    from_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD")
):
    """
    获取美股财报日历
    
    - **from_date**: 开始日期，格式 YYYY-MM-DD，默认今天
    - **to_date**: 结束日期，格式 YYYY-MM-DD，默认未来30天
    """
    try:
        sync_service = get_us_fundamental_sync_service()
        earnings = sync_service.get_earnings_calendar(
            from_date=from_date or "",
            to_date=to_date or ""
        )
        
        return {
            "success": True,
            "data": earnings,
            "count": len(earnings),
            "date_range": {"from": from_date, "to": to_date},
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"获取财报日历失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fundamental/sync", summary="同步美股基本面数据")
async def sync_us_stock_fundamental(
    symbols: str = Query(None, description="股票代码列表，逗号分隔，默认同步全部")
):
    """
    手动触发美股基本面数据同步
    
    - **symbols**: 股票代码列表，如 'AAPL,MSFT,GOOGL'，空表示全部11只
    """
    try:
        sync_service = get_us_fundamental_sync_service()
        
        # 解析股票列表
        symbol_list = None
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        results = {}
        if symbol_list:
            # 同步指定股票
            for symbol in symbol_list:
                success = await sync_service.sync_single_stock(symbol)
                results[symbol] = success
        else:
            # 同步全部
            results = await sync_service.sync_all()
        
        success_count = sum(1 for v in results.values() if v)
        fail_count = len(results) - success_count
        
        return {
            "success": fail_count == 0,
            "message": f"同步完成: 成功 {success_count}, 失败 {fail_count}",
            "results": results,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"同步美股基本面失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fundamental/history/{symbol}", summary="获取基本面历史数据")
async def get_us_stock_fundamental_history(
    symbol: str,
    limit: int = Query(30, description="返回条数", ge=1, le=100)
):
    """
    获取美股基本面的历史数据
    
    - **symbol**: 股票代码
    - **limit**: 返回条数，默认30条
    """
    try:
        orm = get_us_stock_fundamental_orm()
        history = orm.get_history(symbol.upper(), limit=limit)
        
        return {
            "success": True,
            "data": history,
            "count": len(history),
            "symbol": symbol.upper(),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"获取 {symbol} 基本面历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", summary="获取基本面同步状态")
async def get_fundamental_status():
    """
    获取所有美股的基本面同步状态
    """
    try:
        sync_service = get_us_fundamental_sync_service()
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
