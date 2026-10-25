"""
依赖注入模块
合并来自 api 和 app/api 的依赖注入配置
统一管理FastAPI依赖注入，提供各层服务的实例获取
"""

from functools import lru_cache
from typing import Optional, Generator
from fastapi import Request

# 导入服务层 - 只保留数据同步相关
from utils.core.config_manager import get_config_manager

# 导入工具和中间件
from utils.api.responses import get_request_id
from api.middleware.rate_limit import get_rate_limiter


# ==================== 请求上下文依赖注入 ====================

def get_current_request_id(request: Request) -> Optional[str]:
    """获取当前请求ID"""
    return get_request_id(request)


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """获取用户代理"""
    return request.headers.get("user-agent", "unknown")


# ==================== 服务层依赖注入 ====================
# 只保留数据同步相关的服务依赖


@lru_cache()
def get_service_config_manager() -> "ServiceConfigManager":
    """获取配置管理器实例（单例）"""
    return get_config_manager()


# ==================== 仓储层依赖注入 ====================
# 只保留数据同步相关的仓储依赖


# ==================== 配置依赖注入 ====================

@lru_cache()
def get_app_settings() -> "AppConfig":
    """获取应用配置实例（单例）"""
    from config.python_config.settings import AppConfig
    return AppConfig()


@lru_cache()
def get_database_settings() -> "DatabaseConfig":
    """获取数据库配置实例（单例）"""
    from config.python_config.settings import DatabaseConfig
    return DatabaseConfig()


@lru_cache()
def get_api_settings() -> "APIConfig":
    """获取API配置实例（单例）"""
    from config.python_config.settings import APIConfig
    return APIConfig()


# ==================== 中间件和工具依赖注入 ====================

@lru_cache()
def get_rate_limiter_instance():
    """获取频率限制器实例（单例）"""
    return get_rate_limiter()


# ==================== 数据库依赖注入 ====================

def get_database_session() -> Generator:
    """
    获取数据库会话（每次请求创建新会话）
    注意：这是一个生成器函数，用于依赖注入
    """
    try:
        # 这里应该根据实际的数据库配置来创建会话
        # 目前项目使用SQLite，可以根据需要实现
        from data.database import get_session
        session = get_session()
        yield session
    except ImportError:
        # 如果数据库模块不存在，返回None
        yield None
    except Exception as e:
        # 记录错误但不中断请求
        print(f"数据库会话创建失败: {e}")
        yield None
    finally:
        # 清理资源
        if 'session' in locals() and session:
            try:
                session.close()
            except Exception:
                pass


# ==================== 组合依赖注入 ====================

class ServiceContainer:
    """服务容器 - 提供统一的服务访问接口"""
    
    def __init__(self):
        self._config_manager = None
    
    @property
    def config_manager(self):
        if self._config_manager is None:
            self._config_manager = get_service_config_manager()
        return self._config_manager


@lru_cache()
def get_service_container() -> ServiceContainer:
    """获取服务容器实例（单例）"""
    return ServiceContainer()


# ==================== 便捷的依赖注入函数 ====================

def get_services() -> ServiceContainer:
    """获取服务容器 - 用于FastAPI依赖注入"""
    return get_service_container()


def get_request_context(request: Request) -> dict:
    """获取请求上下文信息"""
    return {
        "request_id": get_current_request_id(request),
        "client_ip": get_client_ip(request),
        "user_agent": get_user_agent(request),
        "method": request.method,
        "path": str(request.url.path),
        "query_params": dict(request.query_params)
    }
