"""
异常定义模块
定义业务异常类型和全局异常处理器
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import traceback
from utils.core.logger_manager import get_logger


# ==================== 业务异常类 ====================

class QuantTradeException(Exception):
    """量化交易系统基础异常类"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "QUANT_TRADE_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class DataNotFoundError(QuantTradeException):
    """数据未找到异常"""
    
    def __init__(self, resource: str, identifier: str = None, details: Dict[str, Any] = None):
        message = f"未找到{resource}数据"
        if identifier:
            message += f" (标识符: {identifier})"
        super().__init__(message, "DATA_NOT_FOUND", details)


class ValidationError(QuantTradeException):
    """数据验证异常"""
    
    def __init__(self, field: str, value: Any, reason: str = None, details: Dict[str, Any] = None):
        message = f"字段 '{field}' 验证失败"
        if reason:
            message += f": {reason}"
        super().__init__(message, "VALIDATION_ERROR", details)


class ExternalServiceError(QuantTradeException):
    """外部服务异常"""
    
    def __init__(self, service_name: str, operation: str, details: Dict[str, Any] = None):
        message = f"外部服务 {service_name} 的 {operation} 操作失败"
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)


class DatabaseError(QuantTradeException):
    """数据库操作异常"""
    
    def __init__(self, operation: str, table: str = None, details: Dict[str, Any] = None):
        message = f"数据库操作失败: {operation}"
        if table:
            message += f" (表: {table})"
        super().__init__(message, "DATABASE_ERROR", details)


class BusinessLogicError(QuantTradeException):
    """业务逻辑异常"""
    
    def __init__(self, operation: str, reason: str, details: Dict[str, Any] = None):
        message = f"业务逻辑错误: {operation} - {reason}"
        super().__init__(message, "BUSINESS_LOGIC_ERROR", details)


class RateLimitError(QuantTradeException):
    """频率限制异常"""
    
    def __init__(self, limit: int, window: str, details: Dict[str, Any] = None):
        message = f"请求频率超限: {limit}次/{window}"
        super().__init__(message, "RATE_LIMIT_ERROR", details)


# ==================== 异常处理器 ====================

class ExceptionHandler:
    """异常处理器"""
    
    def __init__(self):
        self.logger = get_logger("exceptions.handler")
    
    def handle_quant_trade_exception(self, request: Request, exc: QuantTradeException) -> JSONResponse:
        """处理量化交易系统异常"""
        self.logger.error(f"业务异常: {exc.error_code} - {exc.message}")
        
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": self._get_timestamp()
            }
        )
    
    def handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """处理HTTP异常"""
        self.logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error_code": "HTTP_ERROR",
                "message": str(exc.detail),
                "status_code": exc.status_code,
                "timestamp": self._get_timestamp()
            }
        )
    
    def handle_validation_error(self, request: Request, exc: RequestValidationError) -> JSONResponse:
        """处理请求验证异常"""
        self.logger.warning(f"请求验证失败: {exc.errors()}")
        
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "请求参数验证失败",
                "details": exc.errors(),
                "timestamp": self._get_timestamp()
            }
        )
    
    def handle_general_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """处理通用异常"""
        self.logger.error(f"未处理的异常: {type(exc).__name__} - {str(exc)}")
        self.logger.error(f"异常堆栈: {traceback.format_exc()}")
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": "内部服务器错误",
                "details": {
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc)
                },
                "timestamp": self._get_timestamp()
            }
        )
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()


# ==================== 全局异常处理器注册 ====================

def register_exception_handlers(app):
    """注册全局异常处理器"""
    handler = ExceptionHandler()
    
    # 注册量化交易系统异常处理器
    app.add_exception_handler(QuantTradeException, handler.handle_quant_trade_exception)
    app.add_exception_handler(DataNotFoundError, handler.handle_quant_trade_exception)
    app.add_exception_handler(ValidationError, handler.handle_quant_trade_exception)
    app.add_exception_handler(ExternalServiceError, handler.handle_quant_trade_exception)
    app.add_exception_handler(DatabaseError, handler.handle_quant_trade_exception)
    app.add_exception_handler(BusinessLogicError, handler.handle_quant_trade_exception)
    app.add_exception_handler(RateLimitError, handler.handle_quant_trade_exception)
    
    # 注册HTTP异常处理器
    app.add_exception_handler(HTTPException, handler.handle_http_exception)
    
    # 注册请求验证异常处理器
    app.add_exception_handler(RequestValidationError, handler.handle_validation_error)
    
    # 注册通用异常处理器
    app.add_exception_handler(Exception, handler.handle_general_exception)


# ==================== 异常工具函数 ====================

def raise_data_not_found(resource: str, identifier: str = None, details: Dict[str, Any] = None):
    """抛出数据未找到异常"""
    raise DataNotFoundError(resource, identifier, details)


def raise_validation_error(field: str, value: Any, reason: str = None, details: Dict[str, Any] = None):
    """抛出验证异常"""
    raise ValidationError(field, value, reason, details)


def raise_external_service_error(service_name: str, operation: str, details: Dict[str, Any] = None):
    """抛出外部服务异常"""
    raise ExternalServiceError(service_name, operation, details)


def raise_database_error(operation: str, table: str = None, details: Dict[str, Any] = None):
    """抛出数据库异常"""
    raise DatabaseError(operation, table, details)


def raise_business_logic_error(operation: str, reason: str, details: Dict[str, Any] = None):
    """抛出业务逻辑异常"""
    raise BusinessLogicError(operation, reason, details)


def raise_rate_limit_error(limit: int, window: str, details: Dict[str, Any] = None):
    """抛出频率限制异常"""
    raise RateLimitError(limit, window, details)
