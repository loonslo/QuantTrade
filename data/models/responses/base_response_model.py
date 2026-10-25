"""
统一响应模型
合并来自 api/models 和 app/core/models 的响应模型定义
定义API响应的标准格式
"""

from datetime import datetime
from typing import Any, Dict, Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class BaseResponse(BaseModel, Generic[T]):
    """基础响应模型 - 合并了所有响应模型的通用功能"""
    success: bool
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SuccessResponse(BaseResponse[T]):
    """成功响应模型 - 统一的成功响应格式"""
    success: bool = True
    data: T
    
    def __init__(self, data: T, message: str = "操作成功", request_id: str = None, **kwargs):
        super().__init__(
            success=True,
            data=data,
            message=message,
            request_id=request_id,
            **kwargs
        )


class ErrorResponse(BaseResponse[None]):
    """错误响应模型 - 统一的错误响应格式"""
    success: bool = False
    error_code: str
    details: Dict[str, Any] = Field(default_factory=dict)
    
    def __init__(self, error_code: str, message: str, details: Dict[str, Any] = None, request_id: str = None, **kwargs):
        super().__init__(
            success=False,
            error_code=error_code,
            message=message,
            details=details or {},
            request_id=request_id,
            **kwargs
        )


class ValidationErrorResponse(ErrorResponse):
    """验证错误响应模型 - 专门用于数据验证错误"""
    error_code: str = "VALIDATION_ERROR"
    validation_errors: Dict[str, List[str]] = Field(default_factory=dict)
    
    def __init__(self, message: str = "数据验证失败", validation_errors: Dict[str, List[str]] = None, request_id: str = None, **kwargs):
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=message,
            details={"validation_errors": validation_errors or {}},
            request_id=request_id,
            **kwargs
        )
        self.validation_errors = validation_errors or {}


class PaginatedResponse(BaseResponse[T]):
    """分页响应模型 - 统一的分页响应格式"""
    success: bool = True
    data: T
    pagination: Dict[str, Any]
    
    def __init__(self, data: T, total: int, page: int, page_size: int, 
                 message: str = "获取成功", request_id: str = None, **kwargs):
        # 计算分页信息
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1
        
        pagination = {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev
        }
        
        super().__init__(
            success=True,
            data=data,
            message=message,
            pagination=pagination,
            request_id=request_id,
            **kwargs
        )


class NoContentResponse(BaseResponse[None]):
    """无内容响应模型 - 用于删除等操作"""
    success: bool = True
    data: None = None
    
    def __init__(self, message: str = "操作成功", request_id: str = None, **kwargs):
        super().__init__(
            success=True,
            data=None,
            message=message,
            request_id=request_id,
            **kwargs
        )


class CreatedResponse(SuccessResponse[T]):
    """创建成功响应模型 - 用于资源创建操作"""
    
    def __init__(self, data: T, message: str = "创建成功", request_id: str = None, **kwargs):
        super().__init__(
            data=data,
            message=message,
            request_id=request_id,
            **kwargs
        )


# 响应工厂函数 - 提供便捷的响应创建方法
def success_response(data: Any, message: str = "操作成功", request_id: str = None) -> SuccessResponse:
    """创建成功响应"""
    return SuccessResponse(data=data, message=message, request_id=request_id)


def error_response(error_code: str, message: str, details: Dict[str, Any] = None, request_id: str = None) -> ErrorResponse:
    """创建错误响应"""
    return ErrorResponse(
        error_code=error_code,
        message=message,
        details=details,
        request_id=request_id
    )


def validation_error_response(message: str = "数据验证失败", validation_errors: Dict[str, List[str]] = None, request_id: str = None) -> ValidationErrorResponse:
    """创建验证错误响应"""
    return ValidationErrorResponse(
        message=message,
        validation_errors=validation_errors,
        request_id=request_id
    )


def paginated_response(data: Any, total: int, page: int, page_size: int, message: str = "获取成功", request_id: str = None) -> PaginatedResponse:
    """创建分页响应"""
    return PaginatedResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        message=message,
        request_id=request_id
    )


def no_content_response(message: str = "操作成功", request_id: str = None) -> NoContentResponse:
    """创建无内容响应"""
    return NoContentResponse(message=message, request_id=request_id)


def created_response(data: Any, message: str = "创建成功", request_id: str = None) -> CreatedResponse:
    """创建资源创建成功响应"""
    return CreatedResponse(data=data, message=message, request_id=request_id)


# 常用错误响应快捷方法
def not_found_response(resource: str = "资源", request_id: str = None) -> ErrorResponse:
    """创建资源未找到响应"""
    return error_response(
        error_code="NOT_FOUND",
        message=f"{resource}未找到",
        request_id=request_id
    )


def unauthorized_response(message: str = "未授权访问", request_id: str = None) -> ErrorResponse:
    """创建未授权响应"""
    return error_response(
        error_code="UNAUTHORIZED",
        message=message,
        request_id=request_id
    )


def forbidden_response(message: str = "禁止访问", request_id: str = None) -> ErrorResponse:
    """创建禁止访问响应"""
    return error_response(
        error_code="FORBIDDEN",
        message=message,
        request_id=request_id
    )


def rate_limit_response(retry_after: int = 60, request_id: str = None) -> ErrorResponse:
    """创建频率限制响应"""
    return error_response(
        error_code="RATE_LIMIT_EXCEEDED",
        message="请求过于频繁，请稍后再试",
        details={"retry_after": retry_after},
        request_id=request_id
    )


def internal_error_response(message: str = "内部服务器错误", request_id: str = None) -> ErrorResponse:
    """创建内部错误响应"""
    return error_response(
        error_code="INTERNAL_ERROR",
        message=message,
        request_id=request_id
    )


def bad_request_response(message: str = "请求参数错误", details: Dict[str, Any] = None, request_id: str = None) -> ErrorResponse:
    """创建错误请求响应"""
    return error_response(
        error_code="BAD_REQUEST",
        message=message,
        details=details,
        request_id=request_id
    )