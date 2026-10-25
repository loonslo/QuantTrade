# API Middleware
"""
API Middleware components for QuantTradeSys
合并来自 api/middleware 和 app/api/middleware 的所有中间件功能

This module contains middleware for:
- Authentication and authorization
- CORS handling
- Error handling and logging
- Response formatting
- Rate limiting
- Request/Response processing
"""

from .error_handler import ErrorHandlingMiddleware, RequestLoggingMiddleware, QuantTradeException
from .response_middleware import ResponseFormatterMiddleware
from .response_formatter import ResponseFormatterMiddleware as NewResponseFormatterMiddleware, ResponseHeaderMiddleware
from .cors_middleware import CORSMiddleware
from .rate_limit import rate_limit_middleware, get_rate_limiter
from .setup import (
    setup_middleware, setup_all_middleware, setup_cors_middleware,
    setup_error_handling_middleware, setup_logging_middleware,
    setup_response_middleware, setup_rate_limiting,
    get_development_cors_config, get_production_cors_config
)

__all__ = [
    # 中间件类
    "ErrorHandlingMiddleware",
    "RequestLoggingMiddleware", 
    "ResponseFormatterMiddleware",
    "NewResponseFormatterMiddleware",
    "ResponseHeaderMiddleware",
    "CORSMiddleware",
    
    # 异常类
    "QuantTradeException",
    
    # 中间件函数
    "rate_limit_middleware",
    "get_rate_limiter",
    
    # 设置函数
    "setup_middleware",
    "setup_all_middleware",
    "setup_cors_middleware",
    "setup_error_handling_middleware",
    "setup_logging_middleware", 
    "setup_response_middleware",
    "setup_rate_limiting",
    
    # 配置函数
    "get_development_cors_config",
    "get_production_cors_config"
]