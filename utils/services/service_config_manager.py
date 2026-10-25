"""
服务配置管理器
统一管理服务配置，基于主配置管理器的包装器
"""

from typing import Dict, Any, Optional
from ..core.logger_manager import get_logger
from ..core.config_manager import config_manager


class ServiceConfigManager:
    """服务配置管理器 - 主配置管理器的包装器"""
    
    def __init__(self):
        self.logger = get_logger("services.config_manager")
        self._config_manager = config_manager
        self._default_configs = {
            "market_data": {
                "default_timeframes": ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"],
                "default_limit": 100,
                "max_limit": 1000,
                "cache_ttl": 300,  # 5分钟
                "retry_attempts": 3
            },
            "market_analysis": {
                "default_period": 14,
                "max_period": 200,
                "supported_indicators": ["rsi", "macd", "bollinger", "sma", "ema"],
                "risk_thresholds": {
                    "high_volatility": 10.0,
                    "extreme_volatility": 20.0,
                    "low_volume": 1000000
                }
            },
            "technical_analysis": {
                "rsi_period": 14,
                "macd_fast": 12,
                "macd_slow": 26,
                "macd_signal": 9,
                "bollinger_period": 20,
                "bollinger_std": 2.0
            },
            "data_sync": {
                "batch_size": 100,
                "sync_interval": 300,  # 5分钟
                "max_retries": 3,
                "timeout": 30
            }
        }
    
    def get_config(self, service_name: str) -> Dict[str, Any]:
        """获取服务配置"""
        # 首先尝试从主配置中获取
        main_config = self._config_manager.get(service_name, {})
        
        # 合并默认配置
        default_config = self._default_configs.get(service_name, {}).copy()
        default_config.update(main_config)
        
        return default_config
    
    def get_config_value(self, service_name: str, key: str, default: Any = None) -> Any:
        """获取配置值"""
        # 尝试从主配置获取
        config_key = f"{service_name}.{key}"
        value = self._config_manager.get(config_key)
        
        if value is not None:
            return value
        
        # 从默认配置获取
        service_config = self._default_configs.get(service_name, {})
        return service_config.get(key, default)
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return self._config_manager.get("database", {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self._config_manager.get("api", {})



# 全局配置管理器实例
_config_manager: Optional[ServiceConfigManager] = None

def get_config_manager() -> ServiceConfigManager:
    """获取配置管理器实例（单例）"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ServiceConfigManager()
    return _config_manager
