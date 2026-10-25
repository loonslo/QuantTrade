"""
API响应工具函数
合并来自 api/utils 和 app/api/utils 的响应创建功能
提供便捷的响应创建方法
"""

from typing import Any, Dict, Optional, List
from fastapi import Request
from fastapi.responses import JSONResponse
from datetime import datetime
from utils.time.format_utils import format_timestamp

# 使用内置响应实现
USE_RESPONSE_MODELS = False


def get_request_id(request: Request) -> Optional[str]:
    """获取请求ID"""
    return getattr(request.state, 'request_id', None)


def create_success_response(
    data: Any,
    message: str = "操作成功",
    request: Optional[Request] = None,
    status_code: int = 200
) -> JSONResponse:
    """
    创建成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        request: 请求对象
        status_code: HTTP状态码
        
    Returns:
        JSON响应
    """
    request_id = get_request_id(request) if request else None
    
    response_content = {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": format_timestamp(datetime.now())
    }
    
    if request_id:
        response_content["request_id"] = request_id
    
    return JSONResponse(
        content=response_content,
        status_code=status_code
    )


def create_error_response(
    error_code: str,
    message: str,
    details: Dict[str, Any] = None,
    status_code: int = 400,
    request: Optional[Request] = None
) -> JSONResponse:
    """
    创建错误响应
    
    Args:
        error_code: 错误码
        message: 错误消息
        details: 错误详情
        status_code: HTTP状态码
        request: 请求对象
        
    Returns:
        JSON响应
    """
    request_id = get_request_id(request) if request else None
    
    response_content = {
        "success": False,
        "error_code": error_code,
        "message": message,
        "details": details or {},
        "timestamp": format_timestamp(datetime.now())
    }
    
    if request_id:
        response_content["request_id"] = request_id
    
    return JSONResponse(
        content=response_content,
        status_code=status_code
    )


def create_paginated_response(
    data: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "获取成功",
    request: Optional[Request] = None
) -> JSONResponse:
    """
    创建分页响应
    
    Args:
        data: 响应数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页大小
        message: 响应消息
        request: 请求对象
        
    Returns:
        JSON响应
    """
    request_id = get_request_id(request) if request else None
    
    # 计算分页信息
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    has_next = page < total_pages
    has_prev = page > 1
    
    response_content = {
        "success": True,
        "data": data,
        "message": message,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_prev": has_prev
        },
        "timestamp": format_timestamp(datetime.now())
    }
    
    if request_id:
        response_content["request_id"] = request_id
    
    return JSONResponse(
        content=response_content,
        status_code=200
    )


def create_no_content_response(
    message: str = "操作成功",
    request: Optional[Request] = None
) -> JSONResponse:
    """
    创建无内容响应
    
    Args:
        message: 响应消息
        request: 请求对象
        
    Returns:
        JSON响应
    """
    request_id = get_request_id(request) if request else None
    
    response_content = {
        "success": True,
        "data": None,
        "message": message,
        "timestamp": format_timestamp(datetime.now())
    }
    
    if request_id:
        response_content["request_id"] = request_id
    
    return JSONResponse(
        content=response_content,
        status_code=204
    )


def create_created_response(
    data: Any,
    message: str = "创建成功",
    request: Optional[Request] = None
) -> JSONResponse:
    """
    创建资源创建成功响应
    
    Args:
        data: 创建的资源数据
        message: 响应消息
        request: 请求对象
        
    Returns:
        JSON响应
    """
    return create_success_response(
        data=data,
        message=message,
        request=request,
        status_code=201
    )


def create_validation_error_response(
    field_errors: Dict[str, List[str]],
    message: str = "数据验证失败",
    request: Optional[Request] = None
) -> JSONResponse:
    """
    创建验证错误响应
    
    Args:
        field_errors: 字段错误信息
        message: 错误消息
        request: 请求对象
        
    Returns:
        JSON响应
    """
    return create_error_response(
        error_code="VALIDATION_ERROR",
        message=message,
        details={"field_errors": field_errors},
        status_code=422,
        request=request
    )


def create_not_found_response(
    resource: str = "资源",
    request: Optional[Request] = None
) -> JSONResponse:
    """
    创建资源未找到响应
    
    Args:
        resource: 资源名称
        request: 请求对象
        
    Returns:
        JSON响应
    """
    return create_error_response(
        error_code="NOT_FOUND",
        message=f"{resource}未找到",
        status_code=404,
        request=request
    )


def create_unauthorized_response(
    message: str = "未授权访问",
    request: Optional[Request] = None
) -> JSONResponse:
    """
    创建未授权响应
    
    Args:
        message: 错误消息
        request: 请求对象
        
    Returns:
        JSON响应
    """
    return create_error_response(
        error_code="UNAUTHORIZED",
        message=message,
        status_code=401,
        request=request
    )


def create_forbidden_response(
    message: str = "禁止访问",
    request: Optional[Request] = None
) -> JSONResponse:
    """
    创建禁止访问响应
    
    Args:
        message: 错误消息
        request: 请求对象
        
    Returns:
        JSON响应
    """
    return create_error_response(
        error_code="FORBIDDEN",
        message=message,
        status_code=403,
        request=request
    )


def create_rate_limit_response(
    retry_after: int = 60,
    request: Optional[Request] = None
) -> JSONResponse:
    """
    创建频率限制响应
    
    Args:
        retry_after: 重试等待时间（秒）
        request: 请求对象
        
    Returns:
        JSON响应
    """
    response = create_error_response(
        error_code="RATE_LIMIT_EXCEEDED",
        message="请求过于频繁，请稍后再试",
        details={"retry_after": retry_after},
        status_code=429,
        request=request
    )
    
    # 添加频率限制相关的响应头
    response.headers["Retry-After"] = str(retry_after)
    
    return response


# 兼容性别名
create_response = create_success_response