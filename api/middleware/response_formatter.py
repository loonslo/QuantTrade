"""
响应格式化中间件
统一API响应格式
"""

import json
from typing import Callable, Any, Optional
from datetime import datetime
from utils.time.format_utils import format_timestamp

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# 尝试导入响应模型，如果不存在则使用内置实现
try:
    from models.responses.base_response import SuccessResponse
    USE_RESPONSE_MODELS = True
except ImportError:
    USE_RESPONSE_MODELS = False


class ResponseFormatter:
    """响应格式化器"""

    @staticmethod
    def format_success(data: Any = None, message: str = "操作成功", request_id: Optional[str] = None) -> dict:
        """
        格式化成功响应

        Args:
            data: 响应数据
            message: 成功消息
            request_id: 请求ID

        Returns:
            格式化后的响应字典
        """
        try:
            if USE_RESPONSE_MODELS:
                response = SuccessResponse(
                    data=data,
                    message=message,
                    request_id=request_id
                )
                return response.dict()
            else:
                return {
                    "success": True,
                    "data": data,
                    "message": message,
                    "timestamp": format_timestamp(datetime.now()),
                    "request_id": request_id
                }
        except Exception:
            # 如果格式化失败，返回基本格式
            return {
                "success": True,
                "data": data,
                "message": message,
                "timestamp": format_timestamp(datetime.now())
            }

    @staticmethod
    def format_error(message: str = "操作失败", error_code: int = 500, request_id: Optional[str] = None) -> dict:
        """
        格式化错误响应

        Args:
            message: 错误消息
            error_code: 错误码
            request_id: 请求ID

        Returns:
            格式化后的错误响应字典
        """
        return {
            "success": False,
            "message": message,
            "error_code": error_code,
            "timestamp": format_timestamp(datetime.now()),
            "request_id": request_id
        }


class ResponseFormatterMiddleware(BaseHTTPMiddleware):
    """响应格式化中间件"""
    
    def __init__(self, app, format_responses: bool = True):
        super().__init__(app)
        self.format_responses = format_responses
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """格式化响应"""
        response = await call_next(request)
        
        # 只格式化JSON响应
        if (self.format_responses and 
            isinstance(response, JSONResponse) and 
            response.status_code == 200):
            
            return await self._format_success_response(response, request)
        
        return response
    
    async def _format_success_response(self, response: JSONResponse, request: Request) -> JSONResponse:
        """格式化成功响应"""
        try:
            # 获取原始响应内容
            original_content = json.loads(response.body.decode())
            
            # 检查是否已经是标准格式
            if isinstance(original_content, dict) and "success" in original_content:
                return response
            
            # 格式化为标准响应
            request_id = getattr(request.state, 'request_id', None)
            
            if USE_RESPONSE_MODELS:
                formatted_response = SuccessResponse(
                    data=original_content,
                    message="操作成功",
                    request_id=request_id
                )
                content = formatted_response.dict()
            else:
                # 使用内置格式
                content = {
                    "success": True,
                    "data": original_content,
                    "message": "操作成功",
                    "timestamp": format_timestamp(datetime.now()),
                    "request_id": request_id
                }
            
            return JSONResponse(
                content=content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except Exception:
            # 如果格式化失败，返回原始响应
            return response


class ResponseHeaderMiddleware(BaseHTTPMiddleware):
    """响应头中间件"""
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """添加标准响应头"""
        response = await call_next(request)
        
        # 添加标准响应头
        response.headers["X-API-Version"] = "2.0"
        response.headers["X-Timestamp"] = format_timestamp(datetime.now())
        
        # 添加请求ID到响应头
        request_id = getattr(request.state, 'request_id', None)
        if request_id:
            response.headers["X-Request-ID"] = request_id
        
        return response
