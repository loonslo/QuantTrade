"""
统一错误处理中间件
合并来自 api/middleware 和 app/api/middleware 的错误处理功能
"""

import traceback
import uuid
import time
from datetime import datetime
from typing import Callable, Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.core.logger_manager import get_logger

# 错误代码常量
class ErrorCodes:
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    BUSINESS_ERROR = "BUSINESS_ERROR"


class QuantTradeException(Exception):
    """业务异常基类"""
    
    def __init__(self, message: str, error_code: str = ErrorCodes.BUSINESS_ERROR, 
                 status_code: int = 400, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """统一错误处理中间件 - 合并了所有错误处理功能"""
    
    def __init__(self, app, debug: bool = False):
        super().__init__(app)
        self.debug = debug
        self.logger = get_logger("middleware.error_handler")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并捕获异常"""
        # 生成请求ID用于追踪
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        try:
            response = await call_next(request)
            return response
            
        except QuantTradeException as e:
            return await self._handle_business_exception(e, request)
            
        except ValueError as e:
            return await self._handle_validation_exception(e, request)
            
        except ConnectionResetError as e:
            return await self._handle_connection_reset_exception(e, request)
            
        except ConnectionError as e:
            return await self._handle_connection_exception(e, request)
            
        except TimeoutError as e:
            return await self._handle_timeout_exception(e, request)
            
        except Exception as e:
            return await self._handle_system_exception(e, request)
    
    async def _handle_business_exception(self, error: QuantTradeException, request: Request) -> JSONResponse:
        """处理业务异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # 记录业务异常日志
        self.logger.warning(
            f"Business exception: {error.message}",
            extra={
                "error_code": error.error_code,
                "request_id": request_id,
                "path": str(request.url),
                "method": request.method,
                "details": error.details
            }
        )
        
        error_response = {
            "success": False,
            "error_code": error.error_code,
            "message": error.message,
            "details": error.details,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id
        }
        
        # 在调试模式下添加堆栈跟踪
        if self.debug:
            error_response["traceback"] = traceback.format_exc()
        
        return JSONResponse(
            status_code=error.status_code,
            content=error_response
        )
    
    async def _handle_validation_exception(self, error: ValueError, request: Request) -> JSONResponse:
        """处理验证异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        self.logger.warning(
            f"Validation error: {str(error)}",
            extra={
                "error_code": "VALIDATION_ERROR",
                "request_id": request_id,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        error_response = {
            "success": False,
            "error_code": "VALIDATION_ERROR",
            "message": str(error),
            "details": {},
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id
        }
        
        if self.debug:
            error_response["traceback"] = traceback.format_exc()
        
        return JSONResponse(
            status_code=400,
            content=error_response
        )
    
    async def _handle_connection_exception(self, error: ConnectionError, request: Request) -> JSONResponse:
        """处理连接异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        self.logger.error(
            f"Connection error: {str(error)}",
            extra={
                "error_code": "NETWORK_ERROR",
                "request_id": request_id,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        error_response = {
            "success": False,
            "error_code": "NETWORK_ERROR",
            "message": "网络连接错误",
            "details": {"original_error": str(error)},
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id
        }
        
        if self.debug:
            error_response["traceback"] = traceback.format_exc()
        
        return JSONResponse(
            status_code=502,
            content=error_response
        )
    
    async def _handle_connection_reset_exception(self, error: ConnectionResetError, request: Request) -> JSONResponse:
        """处理连接重置异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        self.logger.warning(
            f"Connection reset error: {str(error)}",
            extra={
                "error_code": "CONNECTION_RESET_ERROR",
                "request_id": request_id,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        error_response = {
            "success": False,
            "error_code": "CONNECTION_RESET_ERROR",
            "message": "连接被重置，请重试",
            "details": {"original_error": str(error)},
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id
        }
        
        if self.debug:
            error_response["traceback"] = traceback.format_exc()
        
        return JSONResponse(
            status_code=503,
            content=error_response
        )

    async def _handle_timeout_exception(self, error: TimeoutError, request: Request) -> JSONResponse:
        """处理超时异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        self.logger.error(
            f"Timeout error: {str(error)}",
            extra={
                "error_code": "TIMEOUT_ERROR",
                "request_id": request_id,
                "path": str(request.url),
                "method": request.method
            }
        )
        
        error_response = {
            "success": False,
            "error_code": "TIMEOUT_ERROR",
            "message": "请求超时",
            "details": {"original_error": str(error)},
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id
        }
        
        if self.debug:
            error_response["traceback"] = traceback.format_exc()
        
        return JSONResponse(
            status_code=504,
            content=error_response
        )
    
    async def _handle_system_exception(self, error: Exception, request: Request) -> JSONResponse:
        """处理系统异常"""
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # 记录系统异常日志
        self.logger.critical(
            f"System exception: {str(error)}",
            extra={
                "error_code": "INTERNAL_ERROR",
                "request_id": request_id,
                "path": str(request.url),
                "method": request.method,
                "exception_type": type(error).__name__,
                "traceback": traceback.format_exc()
            }
        )
        
        error_response = {
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "message": "系统内部错误",
            "details": {},
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id
        }
        
        # 在调试模式下显示详细错误信息
        if self.debug:
            error_response["details"] = {
                "exception_type": type(error).__name__,
                "original_error": str(error)
            }
            error_response["traceback"] = traceback.format_exc()
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件 - 合并了原有的日志功能"""
    
    def __init__(self, app, log_details: bool = True, log_response_body: bool = True, max_body_size: int = 1024):
        super().__init__(app)
        self.logger = get_logger("middleware.logging")
        self.log_details = log_details  # 是否记录详细参数
        self.log_response_body = log_response_body  # 是否记录响应体
        self.max_body_size = max_body_size  # 最大响应体大小
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """记录请求和响应日志"""
        # 生成请求ID（如果还没有的话）
        if not hasattr(request.state, 'request_id'):
            request.state.request_id = str(uuid.uuid4())
        
        request_id = request.state.request_id
        start_time = time.time()
        
        # 记录请求开始
        await self._log_request(request, request_id)
        
        try:
            response = await call_next(request)
            
            # 拦截并缓存响应内容
            response_body = None
            if self.log_response_body and hasattr(response, 'body_iterator'):
                # 读取响应体
                body_parts = []
                async for chunk in response.body_iterator:
                    body_parts.append(chunk)
                response_body = b''.join(body_parts)
                
                # 重新创建响应迭代器
                response.body_iterator = self._create_body_iterator(response_body)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息（包含body）
            await self._log_response(request, response, request_id, process_time, response_body)
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录异常信息
            await self._log_exception(request, e, request_id, process_time)
            
            raise
    
    def _create_body_iterator(self, body: bytes):
        """创建响应体迭代器"""
        async def generate():
            yield body
        return generate()
    
    async def _log_request(self, request: Request, request_id: str):
        """记录请求信息"""
        try:
            # 获取客户端IP
            client_ip = request.client.host if request.client else "unknown"
            
            # 获取用户代理
            user_agent = request.headers.get("user-agent", "unknown")
            
            # 获取请求参数
            request_params = await self._get_request_params(request)
            
            # 记录请求日志
            self.logger.info(
                f"请求开始 - ID: {request_id}, "
                f"方法: {request.method}, "
                f"路径: {request.url.path}, "
                f"查询参数: {dict(request.query_params)}, "
                f"客户端IP: {client_ip}, "
                f"用户代理: {user_agent[:100]}"
            )
            
            # 单独记录请求参数（如果有的话）
            if self.log_details and request_params:
                self.logger.info(
                    f"请求参数 - ID: {request_id}, "
                    f"参数: {request_params}"
                )
            
        except Exception as e:
            self.logger.error(f"记录请求日志失败: {e}")
    
    async def _get_request_params(self, request: Request) -> dict:
        """获取请求参数"""
        try:
            params = {}
            
            # 获取路径参数
            if hasattr(request, 'path_params') and request.path_params:
                params['path_params'] = request.path_params
            
            # 获取查询参数
            if request.query_params:
                params['query_params'] = dict(request.query_params)
            
            # 获取请求体（仅对POST/PUT/PATCH请求）
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    # 读取请求体
                    body = await request.body()
                    if body:
                        # 尝试解析JSON
                        import json
                        try:
                            params['body'] = json.loads(body.decode('utf-8'))
                        except json.JSONDecodeError:
                            # 如果不是JSON，记录原始数据（截断）
                            params['body'] = body.decode('utf-8')[:500] + "..." if len(body) > 500 else body.decode('utf-8')
                except Exception as e:
                    params['body_error'] = str(e)
            
            # 获取请求头（过滤敏感信息）
            headers = {}
            sensitive_headers = ['authorization', 'cookie', 'x-api-key']
            for key, value in request.headers.items():
                if key.lower() not in sensitive_headers:
                    headers[key] = value
                else:
                    headers[key] = "***"
            if headers:
                params['headers'] = headers
            
            return params
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _log_response(self, request: Request, response: Response, 
                          request_id: str, process_time: float, response_body: bytes = None):
        """记录响应信息"""
        try:
            # 获取响应内容
            response_content = await self._get_response_content(response, response_body)
            
            # 记录响应日志
            self.logger.info(
                f"请求完成 - ID: {request_id}, "
                f"状态码: {response.status_code}, "
                f"处理时间: {process_time:.3f}s, "
                f"响应大小: {self._get_response_size(response, response_body)} bytes"
            )
            
            # 单独记录响应内容（如果有的话）
            if self.log_details and response_content:
                self.logger.info(
                    f"响应内容 - ID: {request_id}, "
                    f"内容: {response_content}"
                )
            
        except Exception as e:
            self.logger.error(f"记录响应日志失败: {e}")
    
    async def _get_response_content(self, response: Response, response_body: bytes = None) -> dict:
        """获取响应内容"""
        try:
            content_info = {}
            
            # 获取响应头
            if response.headers:
                # 过滤敏感响应头
                sensitive_headers = ['set-cookie', 'authorization']
                headers = {}
                for key, value in response.headers.items():
                    if key.lower() not in sensitive_headers:
                        headers[key] = value
                    else:
                        headers[key] = "***"
                if headers:
                    content_info['headers'] = headers
            
            # 获取响应体
            if response_body and self.log_response_body:
                try:
                    # 限制响应体大小
                    if len(response_body) > self.max_body_size:
                        response_body = response_body[:self.max_body_size]
                    
                    # 尝试解析JSON响应
                    body_str = response_body.decode('utf-8')
                    try:
                        import json
                        parsed_content = json.loads(body_str)
                        content_info['body'] = self._truncate_content(parsed_content)
                    except json.JSONDecodeError:
                        # 如果不是JSON，记录原始内容（截断）
                        content_info['body'] = body_str[:500] + "..." if len(body_str) > 500 else body_str
                except Exception as e:
                    content_info['body_error'] = str(e)
            
            return content_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _truncate_content(self, content, max_length: int = 1000) -> any:
        """截断内容以避免日志过长"""
        try:
            if isinstance(content, dict):
                if len(str(content)) <= max_length:
                    return content
                # 对于字典，保留主要字段
                truncated = {}
                for key, value in content.items():
                    if len(str(truncated)) + len(str(value)) < max_length:
                        truncated[key] = value
                    else:
                        truncated[key] = "..."
                        break
                return truncated
            elif isinstance(content, list):
                if len(str(content)) <= max_length:
                    return content
                # 对于列表，只保留前几个元素
                truncated = content[:3] if len(content) > 3 else content
                if len(content) > 3:
                    truncated.append("...")
                return truncated
            else:
                # 对于其他类型，直接截断字符串
                content_str = str(content)
                return content_str[:max_length] + "..." if len(content_str) > max_length else content_str
        except Exception:
            return str(content)[:max_length] + "..."
    
    async def _log_exception(self, request: Request, exception: Exception, 
                           request_id: str, process_time: float):
        """记录异常信息"""
        try:
            # 记录异常日志
            self.logger.error(
                f"请求异常 - ID: {request_id}, "
                f"异常类型: {type(exception).__name__}, "
                f"异常信息: {str(exception)}, "
                f"处理时间: {process_time:.3f}s"
            )
            
        except Exception as e:
            self.logger.error(f"记录异常日志失败: {e}")
    
    def _get_response_size(self, response: Response, response_body: bytes = None) -> int:
        """获取响应大小"""
        try:
            if response_body:
                return len(response_body)
            # 尝试从headers获取content-length
            content_length = response.headers.get('content-length')
            if content_length:
                return int(content_length)
            return 0
        except Exception:
            return 0