"""
应用配置设置
简化的配置管理，无需额外依赖
"""

import os
from dataclasses import dataclass
from typing import List, Optional


def get_env(key: str, default: str = None) -> str:
    """获取环境变量"""
    return os.getenv(key, default)


def get_env_bool(key: str, default: bool = False) -> bool:
    """获取布尔环境变量"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def get_env_int(key: str, default: int = 0) -> int:
    """获取整数环境变量"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


def get_env_list(key: str, default: List[str] = None) -> List[str]:
    """获取列表环境变量"""
    if default is None:
        default = []
    value = os.getenv(key)
    if not value:
        return default
    return [item.strip() for item in value.split(',') if item.strip()]


@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str = "sqlite:///./quant_trading.db"
    host: str = "localhost"
    port: int = 5432
    name: str = "quant_trading"
    user: str = "postgres"
    password: str = "password"
    pool_size: int = 10
    query_timeout: int = 30

    def __post_init__(self):
        # 从环境变量覆盖默认值
        self.url = get_env("DB_URL", self.url)
        self.host = get_env("DB_HOST", self.host)
        self.port = get_env_int("DB_PORT", self.port)
        self.name = get_env("DB_NAME", self.name)
        self.user = get_env("DB_USER", self.user)
        self.password = get_env("DB_PASSWORD", self.password)
        self.pool_size = get_env_int("DB_POOL_SIZE", self.pool_size)
        self.query_timeout = get_env_int("DB_QUERY_TIMEOUT", self.query_timeout)


@dataclass
class APIConfig:
    """API配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    title: str = "量化交易系统API"
    description: str = "提供量化交易系统的REST API接口"
    version: str = "1.0.0"
    secret_key: str = "your-secret-key-here"
    cors_origins: List[str] = None
    log_details: bool = True  # 是否记录详细的请求和响应参数
    format_responses: bool = True  # 是否格式化响应

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["*"]
        
        # 从环境变量覆盖默认值
        self.host = get_env("API_HOST", self.host)
        self.port = get_env_int("API_PORT", self.port)
        self.title = get_env("API_TITLE", self.title)
        self.description = get_env("API_DESCRIPTION", self.description)
        self.version = get_env("API_VERSION", self.version)
        self.secret_key = get_env("API_SECRET_KEY", self.secret_key)
        self.cors_origins = get_env_list("API_CORS_ORIGINS", self.cors_origins)
        self.log_details = get_env_bool("API_LOG_DETAILS", self.log_details)
        self.format_responses = get_env_bool("API_FORMAT_RESPONSES", self.format_responses)


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    console_output: bool = True

    def __post_init__(self):
        # 从环境变量覆盖默认值
        self.level = get_env("LOG_LEVEL", self.level)
        self.format = get_env("LOG_FORMAT", self.format)
        self.file_path = get_env("LOG_FILE_PATH", self.file_path)
        self.console_output = get_env_bool("LOG_CONSOLE_OUTPUT", self.console_output)


@dataclass
class ExternalServiceConfig:
    """外部服务配置"""
    binance_api_key: Optional[str] = None
    binance_secret_key: Optional[str] = None
    binance_base_url: str = "https://api.binance.com"
    news_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None

    def __post_init__(self):
        # 从环境变量覆盖默认值
        self.binance_api_key = get_env("BINANCE_API_KEY", self.binance_api_key)
        self.binance_secret_key = get_env("BINANCE_SECRET", get_env("BINANCE_SECRET_KEY", self.binance_secret_key))
        self.binance_base_url = get_env("BINANCE_BASE_URL", self.binance_base_url)
        self.news_api_key = get_env("NEWS_API_KEY", self.news_api_key)
        self.finnhub_api_key = get_env("FINNHUB_API_KEY", self.finnhub_api_key)
        self.alpha_vantage_api_key = get_env("ALPHA_VANTAGE_API_KEY", self.alpha_vantage_api_key)


@dataclass
class AppConfig:
    """应用主配置"""
    # 环境配置
    environment: str = "development"
    debug: bool = False
    
    # 子配置
    database: DatabaseConfig = None
    api: APIConfig = None
    logging: LoggingConfig = None
    external_services: ExternalServiceConfig = None
    
    # 应用配置
    app_name: str = "BACKEND"
    app_version: str = "1.0.0"
    
    # 功能开关
    enable_websocket: bool = False
    enable_scheduler: bool = True
    enable_cache: bool = True

    def __post_init__(self):
        # 初始化子配置
        if self.database is None:
            self.database = DatabaseConfig()
        if self.api is None:
            self.api = APIConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.external_services is None:
            self.external_services = ExternalServiceConfig()
        
        # 从环境变量覆盖默认值
        self.environment = get_env("ENVIRONMENT", self.environment)
        self.debug = get_env_bool("DEBUG", self.debug)
        self.app_name = get_env("APP_NAME", self.app_name)
        self.app_version = get_env("APP_VERSION", self.app_version)
        self.enable_websocket = get_env_bool("ENABLE_WEBSOCKET", self.enable_websocket)
        self.enable_scheduler = get_env_bool("ENABLE_SCHEDULER", self.enable_scheduler)
        self.enable_cache = get_env_bool("ENABLE_CACHE", self.enable_cache)
    
    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        if self.database.url.startswith("sqlite"):
            return self.database.url
        else:
            return (
                f"postgresql://{self.database.user}:"
                f"{self.database.password}@"
                f"{self.database.host}:"
                f"{self.database.port}/"
                f"{self.database.name}"
            )
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == "production"


# 全局配置实例
settings = AppConfig()


# 便捷的配置获取函数
def get_settings() -> AppConfig:
    """获取应用配置"""
    return settings


def get_database_config() -> DatabaseConfig:
    """获取数据库配置"""
    return settings.database


def get_api_config() -> APIConfig:
    """获取API配置"""
    return settings.api


def get_logging_config() -> LoggingConfig:
    """获取日志配置"""
    return settings.logging
