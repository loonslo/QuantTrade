"""
策略模型
定义策略相关的请求和响应模型
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class StrategyInfo(BaseModel):
    """策略信息模型"""
    name: str
    description: str
    parameters: Dict[str, Any]
    category: str


class PositionManagerInfo(BaseModel):
    """仓位管理器信息模型"""
    name: str
    description: str
    parameters: Dict[str, Any]
    category: str


class StrategyListResponse(BaseModel):
    """策略列表响应模型"""
    strategies: List[StrategyInfo]
    count: int
    message: str


class PositionManagerListResponse(BaseModel):
    """仓位管理器列表响应模型"""
    position_managers: List[PositionManagerInfo]
    count: int
    message: str


class BacktestRequest(BaseModel):
    """回测请求模型"""
    strategy_name: str = Field(..., description="策略名称", example="simple_ma")
    position_type: str = Field(..., description="仓位管理类型", example="fixed")
    symbol: str = Field(default="BTC/USDT", description="交易对", example="BTC/USDT")
    timeframe: str = Field(default="1h", description="时间间隔", example="1h")
    start_cash: float = Field(default=100000.0, description="初始资金", example=100000.0)
    start_date: Optional[str] = Field(None, description="开始日期", example="2024-01-01")
    end_date: Optional[str] = Field(None, description="结束日期", example="2024-12-31")

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_name": "simple_ma",
                "position_type": "fixed",
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "start_cash": 100000.0,
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        }


class BacktestResult(BaseModel):
    """回测结果模型"""
    strategy_name: str
    position_type: str
    symbol: str
    timeframe: str
    initial_cash: float
    final_cash: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    message: str 