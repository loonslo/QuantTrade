"""
MCP (Model Context Protocol) 数据模型
定义数据帧结构和分析请求/响应模型
"""

from pydantic import BaseModel, Field, field_serializer
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

# 为了向后兼容，定义BaseModelWithDateTime
BaseModelWithDateTime = BaseModel


class DataFrameType(str, Enum):
    """数据帧类型枚举"""
    OHLCV = "ohlcv"           # K线数据
    TRADE = "trade"           # 交易数据
    ORDERBOOK = "orderbook"   # 订单簿数据
    TICKER = "ticker"         # 行情数据
    NEWS = "news"             # 新闻数据
    SENTIMENT = "sentiment"   # 情绪数据
    TECHNICAL = "technical"   # 技术指标
    FUNDAMENTAL = "fundamental"  # 基本面数据


class DataFrame(BaseModelWithDateTime):
    """数据帧基础模型"""
    frame_id: str = Field(..., description="数据帧唯一标识")
    frame_type: DataFrameType = Field(..., description="数据帧类型")
    symbol: str = Field(..., description="交易对符号")
    timeframe: Optional[str] = Field(None, description="时间框架")
    timestamp: datetime = Field(..., description="数据时间戳")
    data: Dict[str, Any] = Field(..., description="具体数据内容")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="元数据信息")
    quality_score: Optional[float] = Field(None, ge=0, le=1, description="数据质量评分")


class OHLCVFrame(BaseModel):
    """OHLCV数据帧模型"""
    datetime: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    additional_data: Optional[Dict[str, Any]] = Field(default={}, description="额外数据")


class TechnicalIndicatorFrame(BaseModel):
    """技术指标数据帧模型"""
    indicator_name: str = Field(..., description="指标名称")
    values: List[float] = Field(..., description="指标值")
    timestamps: List[str] = Field(..., description="对应时间戳")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="指标参数")


class SentimentFrame(BaseModel):
    """情绪数据帧模型"""
    fear_greed_index: Optional[int] = Field(None, description="恐惧贪婪指数")
    sentiment_score: Optional[float] = Field(None, description="情绪评分")
    sentiment_label: Optional[str] = Field(None, description="情绪标签")
    confidence: Optional[float] = Field(None, description="置信度")


class NewsFrame(BaseModelWithDateTime):
    """新闻数据帧模型"""
    title: str = Field(..., description="新闻标题")
    content: str = Field(..., description="新闻内容")
    source: str = Field(..., description="新闻来源")
    published_at: datetime = Field(..., description="发布时间")
    sentiment: Optional[str] = Field(None, description="新闻情绪")
    impact_score: Optional[float] = Field(None, description="影响评分")


class MCPAnalysisRequest(BaseModel):
    """MCP分析请求模型"""
    request_id: str = Field(..., description="请求唯一标识")
    analysis_type: str = Field(..., description="分析类型")
    data_frames: List[DataFrame] = Field(..., description="待分析的数据帧列表")
    analysis_parameters: Optional[Dict[str, Any]] = Field(default={}, description="分析参数")
    priority: Optional[str] = Field(default="normal", description="分析优先级")
    callback_url: Optional[str] = Field(None, description="回调URL")


class MarketTrendAnalysis(BaseModel):
    """市场趋势分析结果"""
    trend_direction: str = Field(..., description="趋势方向")
    trend_strength: float = Field(..., description="趋势强度")
    support_levels: List[float] = Field(default=[], description="支撑位")
    resistance_levels: List[float] = Field(default=[], description="阻力位")
    confidence: float = Field(..., description="分析置信度")
    key_insights: List[str] = Field(default=[], description="关键洞察")


class RiskAssessment(BaseModel):
    """风险评估结果"""
    risk_level: str = Field(..., description="风险等级")
    risk_score: float = Field(..., description="风险评分")
    risk_factors: List[str] = Field(default=[], description="风险因素")
    volatility_forecast: Optional[float] = Field(None, description="波动率预测")
    drawdown_risk: Optional[float] = Field(None, description="回撤风险")


class TradingSignal(BaseModel):
    """交易信号结果"""
    signal_type: str = Field(..., description="信号类型")
    signal_strength: float = Field(..., description="信号强度")
    entry_price: Optional[float] = Field(None, description="入场价格")
    stop_loss: Optional[float] = Field(None, description="止损价格")
    take_profit: Optional[float] = Field(None, description="止盈价格")
    confidence: float = Field(..., description="信号置信度")


class MCPAnalysisResult(BaseModelWithDateTime):
    """MCP分析结果模型"""
    analysis_id: str = Field(..., description="分析唯一标识")
    request_id: str = Field(..., description="对应请求ID")
    analysis_type: str = Field(..., description="分析类型")
    timestamp: datetime = Field(..., description="分析完成时间")
    processing_time_ms: float = Field(..., description="处理时间(毫秒)")
    
    # 分析结果
    market_trend: Optional[MarketTrendAnalysis] = Field(None, description="市场趋势分析")
    risk_assessment: Optional[RiskAssessment] = Field(None, description="风险评估")
    trading_signals: Optional[List[TradingSignal]] = Field(None, description="交易信号")
    
    # 综合结果
    summary: str = Field(..., description="分析摘要")
    recommendations: List[str] = Field(default=[], description="投资建议")
    confidence_overall: float = Field(..., description="整体置信度")
    
    # 元数据
    data_quality_report: Optional[Dict[str, Any]] = Field(None, description="数据质量报告")
    model_metadata: Optional[Dict[str, Any]] = Field(None, description="模型元数据")


class MCPAnalysisResponse(BaseModel):
    """MCP分析响应模型"""
    success: bool = Field(..., description="请求是否成功")
    data: MCPAnalysisResult = Field(..., description="分析结果数据")
    message: str = Field(..., description="响应消息")
    error_code: Optional[str] = Field(None, description="错误代码")


class MCPStatusResponse(BaseModel):
    """MCP服务状态响应模型"""
    service_name: str = Field(..., description="服务名称")
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="服务版本")
    uptime: str = Field(..., description="运行时间")
    active_analyses: int = Field(..., description="活跃分析数量")
    total_analyses: int = Field(..., description="总分析数量")
    performance_metrics: Dict[str, Any] = Field(default={}, description="性能指标")
