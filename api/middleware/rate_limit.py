"""
请求频率限制中间件
防止API被过度调用
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import time
from collections import defaultdict, deque
from typing import Dict, Deque
import asyncio


class RateLimiter:
    """请求频率限制器"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        """
        初始化频率限制器
        
        Args:
            max_requests: 时间窗口内最大请求数
            time_window: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, Deque[float]] = defaultdict(deque)
        self.lock = asyncio.Lock()
        
        # 不同端点的限流配置
        self.endpoint_limits = {
            "/api/market-data/batch/prices": {"max_requests": 30, "time_window": 60},  # 批量价格查询限制更严格
            "/api/market-data/strategy-allocation": {"max_requests": 10, "time_window": 60},  # 策略配置查询限制
            "/api/support-resistance": {"max_requests": 20, "time_window": 60},  # 支撑阻力位查询
        }
    
    async def is_allowed(self, client_ip: str, endpoint: str = None) -> bool:
        """
        检查客户端是否允许请求
        
        Args:
            client_ip: 客户端IP地址
            endpoint: 请求端点路径
            
        Returns:
            bool: 是否允许请求
        """
        async with self.lock:
            now = time.time()
            
            # 根据端点选择限流配置
            if endpoint and endpoint in self.endpoint_limits:
                limit_config = self.endpoint_limits[endpoint]
                max_requests = limit_config["max_requests"]
                time_window = limit_config["time_window"]
                # 使用端点特定的键
                client_key = f"{client_ip}:{endpoint}"
            else:
                max_requests = self.max_requests
                time_window = self.time_window
                client_key = client_ip
            
            client_requests = self.requests[client_key]
            
            # 清理过期的请求记录
            while client_requests and client_requests[0] <= now - time_window:
                client_requests.popleft()
            
            # 检查是否超过限制
            if len(client_requests) >= max_requests:
                return False
            
            # 记录当前请求
            client_requests.append(now)
            return True
    
    def get_remaining_requests(self, client_ip: str, endpoint: str = None) -> int:
        """获取剩余请求次数"""
        now = time.time()
        
        # 根据端点选择限流配置
        if endpoint and endpoint in self.endpoint_limits:
            limit_config = self.endpoint_limits[endpoint]
            max_requests = limit_config["max_requests"]
            time_window = limit_config["time_window"]
            client_key = f"{client_ip}:{endpoint}"
        else:
            max_requests = self.max_requests
            time_window = self.time_window
            client_key = client_ip
        
        client_requests = self.requests[client_key]
        
        # 清理过期的请求记录
        while client_requests and client_requests[0] <= now - time_window:
            client_requests.popleft()
        
        return max(0, max_requests - len(client_requests))


# 全局频率限制器实例 - 调整为更宽松的限制
rate_limiter = RateLimiter(max_requests=200, time_window=60)  # 每分钟最多200个请求


async def rate_limit_middleware(request: Request, call_next):
    """
    频率限制中间件
    
    Args:
        request: FastAPI请求对象
        call_next: 下一个中间件或路由处理器
        
    Returns:
        响应对象
    """
    # 获取客户端IP
    client_ip = request.client.host if request.client else "unknown"
    
    # 跳过OPTIONS请求（CORS预检请求）
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # 跳过健康检查端点
    if request.url.path in ["/health", "/api/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    # 跳过CORS相关的路径
    if request.url.path.startswith("/api/health"):
        return await call_next(request)
    
    # 检查是否允许请求
    endpoint = str(request.url.path)
    if not await rate_limiter.is_allowed(client_ip, endpoint):
        # 获取该端点的限流配置
        if endpoint in rate_limiter.endpoint_limits:
            limit_config = rate_limiter.endpoint_limits[endpoint]
            max_requests = limit_config["max_requests"]
            time_window = limit_config["time_window"]
        else:
            max_requests = rate_limiter.max_requests
            time_window = rate_limiter.time_window
            
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "message": f"请求过于频繁，请稍后再试 (端点: {endpoint})",
                "error_code": "RATE_LIMIT_EXCEEDED"
            },
            headers={
                "Retry-After": str(time_window),
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + time_window))
            }
        )
    
    # 执行请求
    response = await call_next(request)
    
    # 添加频率限制头信息
    remaining = rate_limiter.get_remaining_requests(client_ip, endpoint)
    if endpoint in rate_limiter.endpoint_limits:
        limit_config = rate_limiter.endpoint_limits[endpoint]
        max_requests = limit_config["max_requests"]
        time_window = limit_config["time_window"]
    else:
        max_requests = rate_limiter.max_requests
        time_window = rate_limiter.time_window
        
    response.headers["X-RateLimit-Limit"] = str(max_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(time.time() + time_window))
    
    return response


def get_rate_limiter() -> RateLimiter:
    """获取频率限制器实例"""
    return rate_limiter
