"""
中间件设置和配置
合并来自 api/middleware 和 app/api/middleware 的设置功能
统一的中间件配置和管理
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .error_handler import ErrorHandlingMiddleware, RequestLoggingMiddleware
from .response_middleware import ResponseFormatterMiddleware
from .rate_limit import rate_limit_middleware

# 尝试导入配置管理器
try:
    from utils.core.config_manager import ConfigManager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

# 尝试导入app中间件
try:
    from api.middleware.error_handler import ErrorHandlingMiddleware as AppErrorHandler
    from api.middleware.response_formatter import ResponseFormatterMiddleware as AppResponseFormatter
    APP_MIDDLEWARE_AVAILABLE = True
except ImportError:
    APP_MIDDLEWARE_AVAILABLE = False


def setup_cors_middleware(app: FastAPI) -> None:
    """
    设置CORS中间件
    
    Args:
        app: FastAPI应用实例
    """
    try:
        config = ConfigManager()
        cors_config = config.get_section("cors", {})
    except Exception:
        cors_config = {}
    
    # 默认CORS配置 - 支持前端开发环境
    default_cors = {
        "allow_origins": [
            "http://localhost:3025",  # 前端开发服务器
            "http://127.0.0.1:3025",   # 前端开发服务器备用地址
            "http://localhost:3000",   # 常见前端端口
            "http://127.0.0.1:3000",   # 常见前端端口备用
            "http://localhost:5173",   # Vite默认端口
            "http://127.0.0.1:5173",   # Vite默认端口备用
            "*"  # 开发环境允许所有来源
        ],
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-CSRFToken",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ]
    }
    
    # 合并配置
    cors_settings = {**default_cors, **cors_config}
    
    app.add_middleware(CORSMiddleware, **cors_settings)
    
    print("CORS中间件设置完成")
    print(f"   允许的来源: {cors_settings['allow_origins']}")
    print(f"   允许的方法: {cors_settings['allow_methods']}")
    print(f"   允许的头部: {cors_settings['allow_headers']}")


def setup_rate_limiting(app: FastAPI) -> None:
    """
    设置频率限制中间件
    
    Args:
        app: FastAPI应用实例
    """
    app.middleware("http")(rate_limit_middleware)
    print("频率限制中间件设置完成")


def setup_response_middleware(app: FastAPI) -> None:
    """
    设置响应格式化中间件
    
    Args:
        app: FastAPI应用实例
    """
    try:
        config = ConfigManager()
        format_responses = config.get("api.format_responses", True)
    except Exception:
        format_responses = True
    
    app.add_middleware(ResponseFormatterMiddleware, format_responses=format_responses)
    print(f"响应格式化中间件设置完成 (格式化: {format_responses})")


def setup_logging_middleware(app: FastAPI) -> None:
    """
    设置请求日志中间件
    
    Args:
        app: FastAPI应用实例
    """
    try:
        config = ConfigManager()
        log_details = config.get("api.log_details", True)  # 默认记录详细信息
    except Exception:
        log_details = True  # 开发环境默认记录详细信息
    
    app.add_middleware(RequestLoggingMiddleware, log_details=log_details)
    print(f"请求日志中间件设置完成 (详细日志: {log_details})")


def setup_error_handling_middleware(app: FastAPI) -> None:
    """
    设置错误处理中间件
    
    Args:
        app: FastAPI应用实例
    """
    try:
        config = ConfigManager()
        debug_mode = config.get("debug", False)
    except Exception:
        debug_mode = False
    
    app.add_middleware(ErrorHandlingMiddleware, debug=debug_mode)
    print(f"错误处理中间件设置完成 (调试模式: {debug_mode})")


def setup_middleware(app: FastAPI) -> None:
    """
    设置应用中间件
    
    Args:
        app: FastAPI应用实例
    """
    # 添加响应格式化中间件
    setup_response_middleware(app)
    
    # 添加请求日志中间件
    setup_logging_middleware(app)
    
    # 添加错误处理中间件
    setup_error_handling_middleware(app)
    
    print("应用中间件设置完成")


def setup_all_middleware(app: FastAPI, enable_rate_limiting: bool = True) -> None:
    """
    设置所有中间件
    
    Args:
        app: FastAPI应用实例
        enable_rate_limiting: 是否启用频率限制
    """
    # 注意：中间件的添加顺序很重要
    # 后添加的中间件会先执行
    
    # 1. 首先设置CORS（最外层）
    setup_cors_middleware(app)
    
    # 2. 设置频率限制（可选）
    if enable_rate_limiting:
        setup_rate_limiting(app)
    
    # 3. 然后设置应用中间件
    setup_middleware(app)
    
    print("所有中间件设置完成")


def get_development_cors_config() -> dict:
    """获取开发环境CORS配置（宽松配置）"""
    return {
        "allow_origins": ["*"],
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"]
    }


def get_production_cors_config(allowed_origins: list) -> dict:
    """获取生产环境CORS配置（严格配置）"""
    return {
        "allow_origins": allowed_origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["*"]
    }