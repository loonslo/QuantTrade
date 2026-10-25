# -*- coding: utf-8 -*-
"""
美国市场数据API路由
提供纳斯达克、标普500、美元人民币汇率和QDII基金数据的API接口
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from data.orm_services import (
    get_us_market_service,
    get_exchange_rate_service,
    get_qdii_fund_service,
    get_us_stocks_service
)
from services.data_sync.tasks.us_market_sync import get_us_market_sync_service
from services.data_sync.tasks.qdii_fund_sync import get_qdii_fund_sync_service
from services.data_sync.tasks.us_stocks_sync import get_us_stocks_sync_service
from utils.core.logger_manager import get_logger

router = APIRouter(prefix="/us-market", tags=["美国市场数据"])
logger = get_logger("us_market_api")


@router.get("/indices/latest", summary="获取最新的美国市场指数")
async def get_latest_indices():
    """
    获取最新的纳斯达克和标普500指数数据
    """
    try:
        us_market_service = get_us_market_service()
        indices = us_market_service.get_all_latest_indices()
        
        return {
            "success": True,
            "data": indices,
            "count": len(indices),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"获取美国市场指数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indices/{symbol}", summary="获取指定指数数据")
async def get_index_by_symbol(symbol: str):
    """
    获取指定指数的最新数据
    
    - **symbol**: 指数代码 (NASDAQ/SP500)
    """
    try:
        us_market_service = get_us_market_service()
        index_data = us_market_service.get_latest_index(symbol.upper())
        
        if not index_data:
            raise HTTPException(status_code=404, detail=f"未找到指数 {symbol} 的数据")
        
        return {
            "success": True,
            "data": index_data,
            "timestamp": datetime.now()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取指数 {symbol} 数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchange-rate/usdcny", summary="获取美元人民币汇率")
async def get_usdcny_rate():
    """
    获取最新的美元人民币汇率
    """
    try:
        exchange_rate_service = get_exchange_rate_service()
        rate_data = exchange_rate_service.get_latest_rate("USDCNY")
        
        if not rate_data:
            raise HTTPException(status_code=404, detail="未找到美元人民币汇率数据")
        
        return {
            "success": True,
            "data": rate_data,
            "timestamp": datetime.now()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取美元人民币汇率失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/qdii-funds", summary="获取所有QDII基金数据")
async def get_all_qdii_funds(
    fund_type: Optional[str] = Query(None, description="基金类型 (NASDAQ/SP500)")
):
    """
    获取所有QDII基金数据，可按类型筛选
    
    - **fund_type**: 可选，基金类型 (NASDAQ/SP500)
    """
    try:
        qdii_fund_service = get_qdii_fund_service()
        
        if fund_type:
            funds = qdii_fund_service.get_funds_by_type(fund_type.upper())
        else:
            funds = qdii_fund_service.get_all_latest_funds()
        
        return {
            "success": True,
            "data": funds,
            "count": len(funds),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"获取QDII基金数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/qdii-funds/{fund_code}", summary="获取指定基金数据")
async def get_fund_by_code(fund_code: str):
    """
    获取指定基金代码的最新数据
    
    - **fund_code**: 基金代码，如 513100
    """
    try:
        qdii_fund_service = get_qdii_fund_service()
        fund_data = qdii_fund_service.get_latest_fund(fund_code)
        
        if not fund_data:
            raise HTTPException(status_code=404, detail=f"未找到基金 {fund_code} 的数据")
        
        return {
            "success": True,
            "data": fund_data,
            "timestamp": datetime.now()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取基金 {fund_code} 数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/us-market", summary="手动同步美国市场数据")
async def manual_sync_us_market():
    """
    手动触发美国市场数据同步（纳斯达克、标普500、美元人民币汇率）
    """
    try:
        us_market_sync_service = get_us_market_sync_service()
        result = await us_market_sync_service.sync_us_market_data()
        
        return {
            "success": result,
            "message": "美国市场数据同步完成" if result else "美国市场数据同步失败",
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"手动同步美国市场数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/qdii-funds", summary="手动同步QDII基金数据")
async def manual_sync_qdii_funds():
    """
    手动触发QDII基金数据同步
    """
    try:
        qdii_fund_sync_service = get_qdii_fund_sync_service()
        result = await qdii_fund_sync_service.sync_all_qdii_funds()
        
        return {
            "success": result,
            "message": "QDII基金数据同步完成" if result else "QDII基金数据同步失败",
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"手动同步QDII基金数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview", summary="获取美国市场概览")
async def get_us_market_overview():
    """
    获取美国市场概览，包括指数、汇率和基金数据
    """
    try:
        us_market_service = get_us_market_service()
        exchange_rate_service = get_exchange_rate_service()
        qdii_fund_service = get_qdii_fund_service()
        
        # 获取指数数据
        indices = us_market_service.get_all_latest_indices()
        
        # 获取汇率数据
        usdcny = exchange_rate_service.get_latest_rate("USDCNY")
        
        # 获取基金数据统计
        nasdaq_funds = qdii_fund_service.get_funds_by_type("NASDAQ")
        sp500_funds = qdii_fund_service.get_funds_by_type("SP500")
        
        return {
            "success": True,
            "data": {
                "indices": indices,
                "exchange_rate": usdcny,
                "funds": {
                    "nasdaq": {
                        "count": len(nasdaq_funds),
                        "funds": nasdaq_funds
                    },
                    "sp500": {
                        "count": len(sp500_funds),
                        "funds": sp500_funds
                    }
                }
            },
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"获取美国市场概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 美股个股数据 API ==========

@router.post("/us-stocks/sync", summary="同步所有美股数据")
async def sync_all_us_stocks(
    days: int = Query(365, description="获取最近多少天数据", ge=1, le=730)
):
    """
    同步所有11只美股（AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA, JPM, UNH, KO, BRK.B）的日K线数据
    """
    try:
        sync_service = get_us_stocks_sync_service()
        results = await sync_service.sync_all_stocks(days=days)
        
        success_count = sum(1 for v in results.values() if v)
        fail_count = len(results) - success_count
        
        return {
            "success": fail_count == 0,
            "message": f"同步完成: 成功 {success_count}, 失败 {fail_count}",
            "results": results,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"同步所有美股失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/us-stocks/sync/{symbol}", summary="同步单只美股数据")
async def sync_single_us_stock(
    symbol: str,
    days: int = Query(365, description="获取最近多少天数据", ge=1, le=730)
):
    """
    同步单只美股的日K线数据
    
    - **symbol**: 股票代码，如 AAPL, MSFT, GOOGL, AMZN, META, NVDA, TSLA, JPM, UNH, KO, BRK.B
    """
    try:
        sync_service = get_us_stocks_sync_service()
        success = await sync_service.sync_single_stock(symbol.upper(), days=days)
        
        if success:
            # 获取同步后的数据统计
            service = get_us_stocks_service()
            count = service.get_count(symbol.upper())
            date_range = service.get_date_range(symbol.upper())
            latest = service.get_latest(symbol.upper())
            
            return {
                "success": True,
                "message": f"{symbol} 同步成功",
                "data": {
                    "symbol": symbol.upper(),
                    "count": count,
                    "date_range": date_range,
                    "latest": latest
                },
                "timestamp": datetime.now()
            }
        else:
            return {
                "success": False,
                "message": f"{symbol} 同步失败",
                "timestamp": datetime.now()
            }
    except Exception as e:
        logger.error(f"同步 {symbol} 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/us-stocks/latest/{symbol}", summary="获取单只美股最新行情")
async def get_us_stock_latest(symbol: str):
    """
    获取单只美股的最新日K线数据
    
    - **symbol**: 股票代码，如 AAPL, MSFT, GOOGL
    """
    try:
        service = get_us_stocks_service()
        latest = service.get_latest(symbol.upper())
        
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
        logger.error(f"获取 {symbol} 最新行情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/us-stocks/klines/{symbol}", summary="获取美股历史K线")
async def get_us_stock_klines(
    symbol: str,
    start_date: str = Query(..., description="开始日期 YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期 YYYY-MM-DD")
):
    """
    获取美股指定日期范围的历史K线数据
    
    - **symbol**: 股票代码，如 AAPL, MSFT, GOOGL
    - **start_date**: 开始日期，格式 YYYY-MM-DD
    - **end_date**: 结束日期，格式 YYYY-MM-DD
    """
    try:
        service = get_us_stocks_service()
        klines = service.get_klines(symbol.upper(), start_date, end_date)
        
        return {
            "success": True,
            "data": klines,
            "count": len(klines),
            "symbol": symbol.upper(),
            "date_range": {"start": start_date, "end": end_date},
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"获取 {symbol} K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/us-stocks/status", summary="获取美股同步状态")
async def get_us_stocks_status():
    """
    获取所有11只美股的同步状态（数据条数、日期范围、最新价格）
    """
    try:
        sync_service = get_us_stocks_sync_service()
        status = sync_service.get_sync_status()
        
        return {
            "success": True,
            "data": status,
            "count": len(status),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"获取美股同步状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/us-stocks/list", summary="获取美股列表")
async def get_us_stocks_list():
    """
    获取系统支持同步的美股列表
    """
    return {
        "success": True,
        "data": {
            "stocks": [
                {"symbol": "AAPL", "name": "Apple", "sector": "科技"},
                {"symbol": "MSFT", "name": "Microsoft", "sector": "科技"},
                {"symbol": "GOOGL", "name": "Alphabet", "sector": "科技"},
                {"symbol": "AMZN", "name": "Amazon", "sector": "消费"},
                {"symbol": "META", "name": "Meta", "sector": "科技"},
                {"symbol": "NVDA", "name": "NVIDIA", "sector": "科技"},
                {"symbol": "TSLA", "name": "Tesla", "sector": "新能源"},
                {"symbol": "JPM", "name": "JPMorgan Chase", "sector": "金融"},
                {"symbol": "UNH", "name": "联合健康", "sector": "医疗"},
                {"symbol": "KO", "name": "可口可乐", "sector": "消费"},
                {"symbol": "BRK.B", "name": "伯克希尔哈撒韦", "sector": "金融"}
            ],
            "total": 11
        },
        "timestamp": datetime.now()
    }
