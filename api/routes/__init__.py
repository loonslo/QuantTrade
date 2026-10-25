# -*- coding: utf-8 -*-
"""
API Routes Module
所有API路由的统一入口
"""

from fastapi import APIRouter
from .data_sync import router as data_sync_router
from .market import router as market_router
from .config import router as config_router
from .us_market import router as us_market_router
from .crypto_hourly import router as crypto_hourly_router
from .us_fundamental import router as us_fundamental_router
from .risk_control import router as risk_control_router
from .backtests import router as backtests_router

# Create main API router
api_router = APIRouter(prefix="/api")

# Include all route modules
api_router.include_router(data_sync_router, tags=["数据同步"])
api_router.include_router(market_router, tags=["市场数据"])
api_router.include_router(config_router, tags=["系统配置"])
api_router.include_router(us_market_router, tags=["基金数据"])
api_router.include_router(crypto_hourly_router, tags=["加密货币小时K线"])
api_router.include_router(us_fundamental_router, tags=["美股基本面数据"])
api_router.include_router(risk_control_router, tags=["风控监控"])
api_router.include_router(backtests_router)

__all__ = ["api_router"]
