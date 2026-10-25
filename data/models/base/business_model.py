"""
业务数据模型
定义用于API和业务逻辑的Pydantic模型
"""

from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, field_serializer, ConfigDict
from decimal import Decimal


class BaseBusinessModel(BaseModel):
    """基础业务模型"""
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v else None
        },
        validate_assignment=True,
        use_enum_values=True
    )


# 市场数据相关模型
class MarketDataPoint(BaseBusinessModel):
    """市场数据点模型"""
    timestamp: str = Field(..., description="时间戳")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")


class MarketDataRequest(BaseBusinessModel):
    """市场数据请求模型"""
    symbol: str = Field(..., description="交易对，如 BTC/USDT", example="BTC/USDT")
    timeframe: str = Field(default="1m", description="时间间隔", example="1h")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    limit: Optional[int] = Field(default=500, ge=1, le=1000, description="数据条数限制")


class MarketDataResponse(BaseBusinessModel):
    """市场数据响应模型"""
    symbol: str
    timeframe: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    data_count: int
    data: List[MarketDataPoint]


class LatestPriceResponse(BaseBusinessModel):
    """最新价格响应模型"""
    symbol: str
    price: float
    change_24h: float = Field(..., description="24小时涨跌幅百分比")
    timestamp: datetime


# 币种相关模型
class CoinOverviewData(BaseBusinessModel):
    """币种概览数据模型"""
    price: str = Field(..., description="价格")
    change_24h: str = Field(..., description="24小时涨跌幅")
    change_amount: str = Field(..., description="涨跌金额")
    market_cap: str = Field(..., description="市值")
    volume_24h: str = Field(..., description="24小时成交量")
    trend_chart_data: List[MarketDataPoint] = Field(default=[], description="趋势图表数据")


class CoinDetailsData(BaseBusinessModel):
    """币种技术分析数据模型（基于真实技术指标计算）"""
    symbol: str = Field(..., description="交易对符号")
    
    # 时间维度
    analysis_timestamp: datetime = Field(..., description="分析时间戳")
    data_start_time: datetime = Field(..., description="数据开始时间")
    data_end_time: datetime = Field(..., description="数据结束时间")
    timeframe: str = Field(default="3m", description="分析时间周期")
    
    # 趋势分析（基于技术指标计算）
    trend: Optional[str] = Field(None, description="趋势(bullish/bearish/neutral)")
    trend_strength: Optional[float] = Field(None, ge=0, le=1, description="趋势强度(0-1)")
    trend_confidence: Optional[float] = Field(None, ge=0, le=1, description="趋势置信度(0-1)")
    
    # 支撑位（2级）
    support_1: Optional[float] = Field(None, description="第一支撑位")
    support_1_strength: Optional[float] = Field(None, ge=0, le=1, description="第一支撑位强度(0-1)")
    support_1_confidence: Optional[float] = Field(None, ge=0, le=1, description="第一支撑位置信度(0-1)")
    
    support_2: Optional[float] = Field(None, description="第二支撑位")
    support_2_strength: Optional[float] = Field(None, ge=0, le=1, description="第二支撑位强度(0-1)")
    support_2_confidence: Optional[float] = Field(None, ge=0, le=1, description="第二支撑位置信度(0-1)")
    
    # 阻力位（2级）
    resistance_1: Optional[float] = Field(None, description="第一阻力位")
    resistance_1_strength: Optional[float] = Field(None, ge=0, le=1, description="第一阻力位强度(0-1)")
    resistance_1_confidence: Optional[float] = Field(None, ge=0, le=1, description="第一阻力位置信度(0-1)")
    
    resistance_2: Optional[float] = Field(None, description="第二阻力位")
    resistance_2_strength: Optional[float] = Field(None, ge=0, le=1, description="第二阻力位强度(0-1)")
    resistance_2_confidence: Optional[float] = Field(None, ge=0, le=1, description="第二阻力位置信度(0-1)")
    
    # 技术指标快照（用于趋势分析）
    current_price: Optional[float] = Field(None, description="当前价格")
    ema20: Optional[float] = Field(None, description="20期EMA")
    ema50: Optional[float] = Field(None, description="50期EMA")
    rsi: Optional[float] = Field(None, ge=0, le=100, description="RSI指标")
    macd: Optional[float] = Field(None, description="MACD指标")
    atr: Optional[float] = Field(None, ge=0, description="ATR指标")
    
    # 数据状态
    is_valid: bool = Field(default=True, description="数据是否有效")
    is_latest: bool = Field(default=True, description="是否最新数据")
    data_quality: Optional[float] = Field(None, ge=0, le=1, description="数据质量评分(0-1)")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


# 技术指标相关模型
class TechnicalIndicatorsData(BaseBusinessModel):
    """技术指标数据模型"""
    symbol: str = Field(..., description="交易对符号")
    timeframe: str = Field(default="3min", description="时间周期")
    timestamp: str = Field(..., description="时间戳")
    
    # EMA指标
    ema20: Optional[float] = Field(None, description="20期EMA值")
    ema50: Optional[float] = Field(None, description="50期EMA值")
    
    # MACD指标
    macd_intraday: Optional[float] = Field(None, description="日内周期MACD值")
    macd_4h: Optional[float] = Field(None, description="4小时周期MACD值")
    
    # RSI指标
    rsi7: Optional[float] = Field(None, ge=0, le=100, description="7期RSI值")
    rsi14: Optional[float] = Field(None, ge=0, le=100, description="14期RSI值")
    
    # ATR指标
    atr3: Optional[float] = Field(None, ge=0, description="3期ATR值")
    atr14: Optional[float] = Field(None, ge=0, description="14期ATR值")
    
    # 合约指标
    open_interest: Optional[float] = Field(None, ge=0, description="永续合约持仓量")
    open_interest_avg: Optional[float] = Field(None, ge=0, description="持仓量平均值")
    funding_rate: Optional[float] = Field(None, description="永续合约资金费率")
    
    # 数据状态
    is_valid: bool = Field(default=True, description="指标数据是否有效")
    source: str = Field(default="binance", description="数据源")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


# 市场情绪相关模型
class MarketSentimentData(BaseBusinessModel):
    """市场情绪数据模型"""
    fear_greed_index: int = Field(..., description="恐惧贪婪指数")
    sentiment: str = Field(..., description="情绪描述")
    classification: str = Field(..., description="情绪分类")
    classification_cn: Optional[str] = Field(None, description="中文情绪分类")
    updated_at: datetime = Field(..., description="更新时间")
    trend: Optional[str] = Field(None, description="情绪变化趋势")


class MarketSummaryData(BaseBusinessModel):
    """市场摘要数据模型"""
    total_market_cap: Optional[str] = Field(None, description="总市值")
    total_volume_24h: Optional[str] = Field(None, description="24小时总成交量")
    market_trend: Optional[str] = Field(None, description="市场趋势")
    risk_level: Optional[str] = Field(None, description="风险等级")
    btc_dominance: Optional[float] = Field(None, description="BTC主导率")
    eth_dominance: Optional[float] = Field(None, description="ETH主导率")
    key_insights: List[str] = Field(default=[], description="关键洞察")


class MarketOverviewData(BaseBusinessModel):
    """市场概览数据模型"""
    btc: Optional[CoinOverviewData] = Field(None, description="比特币数据")
    eth: Optional[CoinOverviewData] = Field(None, description="以太坊数据")
    market_sentiment: Optional[MarketSentimentData] = Field(None, description="市场情绪数据")
    market_summary: Optional[MarketSummaryData] = Field(None, description="市场摘要数据")
    last_updated: datetime = Field(..., description="最后更新时间")


# 交易相关模型
class TradeRecordData(BaseBusinessModel):
    """交易记录数据模型"""
    id: str = Field(..., description="交易ID")
    symbol: str = Field(..., description="交易对")
    side: str = Field(..., description="交易方向", pattern="^(buy|sell)$")
    quantity: float = Field(..., gt=0, description="数量")
    price: float = Field(..., gt=0, description="价格")
    timestamp: datetime = Field(..., description="交易时间")
    commission: float = Field(default=0.0, ge=0, description="手续费")
    pnl: Optional[float] = Field(None, description="盈亏")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    position_id: Optional[str] = Field(None, description="持仓ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


# 策略相关模型
class StrategyInfo(BaseBusinessModel):
    """策略信息模型"""
    name: str = Field(..., description="策略名称")
    description: str = Field(..., description="策略描述")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    category: str = Field(..., description="策略分类")


class BacktestRequest(BaseBusinessModel):
    """回测请求模型"""
    strategy_name: str = Field(..., description="策略名称")
    position_type: str = Field(..., description="仓位管理类型")
    symbol: str = Field(default="BTC/USDT", description="交易对")
    timeframe: str = Field(default="1h", description="时间间隔")
    start_cash: float = Field(default=100000.0, gt=0, description="初始资金")
    start_date: Optional[str] = Field(None, description="开始日期")
    end_date: Optional[str] = Field(None, description="结束日期")


class BacktestResult(BaseBusinessModel):
    """回测结果模型"""
    strategy_name: str
    position_type: str
    symbol: str
    timeframe: str
    initial_cash: float
    final_cash: float
    total_return: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    total_trades: int


# 支撑阻力位相关模型
class SupportResistanceData(BaseBusinessModel):
    """支撑阻力位数据模型（2级）"""
    symbol: str = Field(..., description="交易对符号")
    timeframe: str = Field(..., description="时间周期")
    
    # 支撑位（2级）
    support_1: Optional[float] = Field(None, description="第一支撑位")
    support_1_strength: Optional[float] = Field(None, ge=0, le=1, description="第一支撑位强度")
    support_1_confidence: Optional[float] = Field(None, ge=0, le=1, description="第一支撑位置信度")
    
    support_2: Optional[float] = Field(None, description="第二支撑位")
    support_2_strength: Optional[float] = Field(None, ge=0, le=1, description="第二支撑位强度")
    support_2_confidence: Optional[float] = Field(None, ge=0, le=1, description="第二支撑位置信度")
    
    # 阻力位（2级）
    resistance_1: Optional[float] = Field(None, description="第一阻力位")
    resistance_1_strength: Optional[float] = Field(None, ge=0, le=1, description="第一阻力位强度")
    resistance_1_confidence: Optional[float] = Field(None, ge=0, le=1, description="第一阻力位置信度")
    
    resistance_2: Optional[float] = Field(None, description="第二阻力位")
    resistance_2_strength: Optional[float] = Field(None, ge=0, le=1, description="第二阻力位强度")
    resistance_2_confidence: Optional[float] = Field(None, ge=0, le=1, description="第二阻力位置信度")
    
    # 分析时间
    analysis_time: datetime = Field(..., description="分析时间")
    is_active: bool = Field(default=True, description="是否活跃")


class TradingSignalData(BaseBusinessModel):
    """交易信号数据模型"""
    symbol: str = Field(..., description="交易对符号")
    signal_type: str = Field(..., description="信号类型", pattern="^(BUY|SELL)$")
    entry_price: float = Field(..., gt=0, description="入场价格")
    stop_loss: float = Field(..., gt=0, description="止损价格")
    take_profit: float = Field(..., gt=0, description="止盈价格")
    current_price: Optional[float] = Field(None, description="当前价格")
    confidence: float = Field(..., ge=0, le=1, description="置信度")
    trigger_probability: float = Field(..., ge=0, le=1, description="触发概率")
    expected_return: Optional[float] = Field(None, description="预期收益率")
    risk_reward_ratio: Optional[float] = Field(None, description="风险收益比")
    strategy_name: Optional[str] = Field(None, description="策略名称")
    status: str = Field(default="active", description="状态")
    reasoning: Optional[str] = Field(None, description="信号原因")
    created_at: Optional[datetime] = Field(None, description="创建时间")


# 统一响应模型
class BaseResponse(BaseBusinessModel):
    """基础响应模型"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    request_id: Optional[str] = Field(None, description="请求ID")


class SuccessResponse(BaseResponse):
    """成功响应模型"""
    success: bool = True
    data: Any = Field(..., description="响应数据")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    success: bool = False
    error_code: str = Field(..., description="错误代码")
    details: Dict[str, Any] = Field(default_factory=dict, description="错误详情")


class PaginatedResponse(BaseResponse):
    """分页响应模型"""
    success: bool = True
    data: Any = Field(..., description="响应数据")
    pagination: Dict[str, Any] = Field(..., description="分页信息")


# 响应工厂函数
def success_response(data: Any, message: str = "操作成功", request_id: str = None) -> SuccessResponse:
    """创建成功响应"""
    return SuccessResponse(
        data=data,
        message=message,
        request_id=request_id
    )


def error_response(
    error_code: str,
    message: str,
    details: Dict[str, Any] = None,
    request_id: str = None
) -> ErrorResponse:
    """创建错误响应"""
    return ErrorResponse(
        error_code=error_code,
        message=message,
        details=details or {},
        request_id=request_id
    )


def paginated_response(
    data: Any,
    total: int,
    page: int,
    page_size: int,
    message: str = "获取成功",
    request_id: str = None
) -> PaginatedResponse:
    """创建分页响应"""
    total_pages = (total + page_size - 1) // page_size
    
    pagination = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    
    return PaginatedResponse(
        data=data,
        message=message,
        pagination=pagination,
        request_id=request_id
    )