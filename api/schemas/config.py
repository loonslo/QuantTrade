# -*- coding: utf-8 -*-
"""
系统配置API请求模型
定义系统配置相关的Pydantic模型
"""

from pydantic import BaseModel, Field
from typing import Optional


class CoinListResponse(BaseModel):
    """币种列表响应模型"""
    symbol: str = Field(..., description="交易对符号", example="BTCUSDT")
    base_asset: str = Field(..., description="基础货币", example="BTC")
    quote_asset: str = Field(..., description="计价货币", example="USDT")
    coin_name: Optional[str] = Field(None, description="币种全称", example="Bitcoin")
    coin_symbol: Optional[str] = Field(None, description="币种简称", example="BTC")
    icon_url: Optional[str] = Field(None, description="币种图标URL")
    market_cap: Optional[float] = Field(None, description="市值（美元）", example=1200000000000.0)
