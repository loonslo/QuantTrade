"""
响应格式统一中间件
合并来自 api/middleware 和 app/api/middleware 的响应格式化功能
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Any, Dict, Callable
import json
from datetime import datetime
from utils.time.format_utils import format_timestamp
from utils.core.logger_manager import get_logger


class ResponseFormatterMiddleware(BaseHTTPMiddleware):
    """响应格式化中间件 - 合并了原有的响应格式化功能"""
    
    def __init__(self, app, format_responses: bool = True):
        super().__init__(app)
        self.format_responses = format_responses
        self.logger = get_logger("middleware.response")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求和响应"""
        try:
            # 处理请求
            response = await call_next(request)
            
            # 只格式化成功的JSON响应
            if (self.format_responses and 
                isinstance(response, JSONResponse) and 
                response.status_code == 200):
                
                response = await self._format_success_response(request, response)
            
            # 添加标准响应头
            response = self._add_response_headers(request, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"响应中间件处理失败: {e}")
            return await self._create_error_response(request, e)
    
    async def _format_success_response(self, request: Request, response: JSONResponse) -> JSONResponse:
        """格式化成功响应"""
        try:
            # 获取原始响应内容
            body = response.body
            if isinstance(body, bytes):
                content = json.loads(body.decode('utf-8'))
            else:
                content = body
            
            # 检查是否已经是统一格式
            if isinstance(content, dict) and 'success' in content:
                return response
            
            # 获取请求ID
            request_id = getattr(request.state, 'request_id', None)
            
            # 转换为统一格式
            formatted_content = self._create_success_response_content(content, request_id)
            
            # 创建新的响应
            return JSONResponse(
                content=formatted_content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
        except Exception as e:
            self.logger.error(f"格式化JSON响应失败: {e}")
            return response
    
    def _add_response_headers(self, request: Request, response: Response) -> Response:
        """添加标准响应头"""
        # 添加标准响应头
        response.headers["X-API-Version"] = "2.0"
        response.headers["X-Timestamp"] = format_timestamp(datetime.now())
        
        # 添加请求ID到响应头
        request_id = getattr(request.state, 'request_id', None)
        if request_id:
            response.headers["X-Request-ID"] = request_id
        
        return response
    
    async def _create_error_response(self, request: Request, error: Exception) -> JSONResponse:
        """创建错误响应"""
        request_id = getattr(request.state, 'request_id', None)
        
        return JSONResponse(
            status_code=500,
            content=self._create_error_response_content(error, request_id)
        )
    
    def _create_success_response_content(self, data: Any, request_id: str = None) -> Dict[str, Any]:
        """创建成功响应格式"""
        response_content = {
            "success": True,
            "data": data,
            "message": "请求成功",
            "timestamp": format_timestamp(datetime.now())
        }
        
        if request_id:
            response_content["request_id"] = request_id
        
        return response_content
    
    def _create_error_response_content(self, error: Exception, request_id: str = None) -> Dict[str, Any]:
        """创建错误响应内容"""
        response_content = {
            "success": False,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "内部服务器错误",
            "details": {
                "exception_type": type(error).__name__,
                "exception_message": str(error)
            },
            "timestamp": format_timestamp(datetime.now())
        }
        
        if request_id:
            response_content["request_id"] = request_id
        
        return response_content


# 保持向后兼容性的别名
ResponseMiddleware = ResponseFormatterMiddleware
