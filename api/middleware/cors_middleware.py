"""
CORS中间件
处理跨域请求
"""

from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from typing import List, Optional
from utils.core.logger_manager import get_logger


class CORSMiddleware:
    """CORS中间件配置"""
    
    def __init__(self):
        self.logger = get_logger("middleware.cors")
    
    def get_cors_middleware(self, 
                          app,
                          allow_origins: List[str] = None,
                          allow_credentials: bool = True,
                          allow_methods: List[str] = None,
                          allow_headers: List[str] = None) -> FastAPICORSMiddleware:
        """获取CORS中间件"""
        
        if allow_origins is None:
            allow_origins = ["*"]
        
        if allow_methods is None:
            allow_methods = ["*"]
        
        if allow_headers is None:
            allow_headers = ["*"]
        
        self.logger.info(f"CORS中间件配置: origins={allow_origins}, methods={allow_methods}")
        
        return FastAPICORSMiddleware(
            app=app,
            allow_origins=allow_origins,
            allow_credentials=allow_credentials,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
        )
    
    def get_development_cors_middleware(self, app) -> FastAPICORSMiddleware:
        """获取开发环境CORS中间件（宽松配置）"""
        return self.get_cors_middleware(
            app=app,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
    
    def get_production_cors_middleware(self, app, allowed_origins: List[str]) -> FastAPICORSMiddleware:
        """获取生产环境CORS中间件（严格配置）"""
        return self.get_cors_middleware(
            app=app,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"]
        )
