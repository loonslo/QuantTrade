"""
API Schema模块
定义所有API请求和响应的Pydantic模型
"""

# 通用模型
from .common import (
    BaseModelWithDateTime,
    BaseResponse,
    ErrorResponse,
    PaginationParams,
    PaginationResponse
)

# 市场相关请求模型
from .market import (
    MarketListRequest,
    KlineDataRequest,
    TechnicalIndicatorsRequest,
    TrendDataRequest,
    CryptoFuturesRequest,
    MarketRankRequest,
    SupportResistanceRequest,
    CryptoIndicatorsRequest,
    ShortTemplateRequest,
    FuturesDataRequest,
    OnChainDataRequest
)

# 配置相关模型
from .config import (
    CoinListResponse
)

# 数据同步相关模型
from .data_sync import (
    TechnicalIndicatorRecord
)

__all__ = [
    # 通用模型
    "BaseModelWithDateTime",
    "BaseResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginationResponse",
    # 市场请求模型
    "MarketListRequest",
    "KlineDataRequest",
    "TechnicalIndicatorsRequest",
    "TrendDataRequest",
    "CryptoFuturesRequest",
    "MarketRankRequest",
    "SupportResistanceRequest",
    "CryptoIndicatorsRequest",
    "ShortTemplateRequest",
    "FuturesDataRequest",
    "OnChainDataRequest",
    # 配置模型
    "CoinListResponse",
    # 数据同步模型
    "TechnicalIndicatorRecord"
]
