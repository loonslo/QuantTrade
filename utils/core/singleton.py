"""
单例管理器
用于管理全局单例实例，避免重复创建连接
"""

import json
import os
from typing import Optional, Dict, Any
from .interfaces import SingletonManagerInterface, ToolConfig
from .logger_manager import get_logger


class SingletonManager(SingletonManagerInterface):
    """单例管理器"""
    
    _instances: Dict[str, Any] = {}
    _logger = get_logger('singleton_manager')
    
    def __init__(self):
        # 初始化基类
        config = ToolConfig(
            name="SingletonManager",
            version="1.0.0",
            enabled=True,
            config={}
        )
        super().__init__(config)
    
    @classmethod
    def get_binance_provider(cls, enable_futures: bool = False):
        """获取币安数据提供者单例"""
        # 根据是否启用期货功能使用不同的实例键
        instance_key = 'binance_provider_futures' if enable_futures else 'binance_provider'
        
        if instance_key not in cls._instances:
            from data.providers.binance_provider import BinanceDataProvider
            
            # 从配置文件加载代理设置
            proxies = cls._load_proxy_config()
            
            cls._instances[instance_key] = BinanceDataProvider(
                proxies=proxies, 
                enable_futures=enable_futures
            )
            cls._logger.info(f"✅ 创建币安数据提供者单例 (期货功能: {'启用' if enable_futures else '禁用'})")
        return cls._instances[instance_key]
    
    @classmethod
    def get_technical_analyzer(cls):
        """获取技术分析器单例"""
        if 'technical_analyzer' not in cls._instances:
            from analytics.technical_analysis import TechnicalAnalyzer
            cls._instances['technical_analyzer'] = TechnicalAnalyzer()
            cls._logger.info("✅ 创建技术分析器单例")
        return cls._instances['technical_analyzer']
    
    @classmethod
    def get_support_resistance_storage(cls):
        """获取支撑阻力位存储单例"""
        if 'sr_storage' not in cls._instances:
            from data.storage.support_resistance_storage import SupportResistanceStorage
            cls._instances['sr_storage'] = SupportResistanceStorage()
            cls._logger.info("✅ 创建支撑阻力位存储单例")
        return cls._instances['sr_storage']
    
    @classmethod
    def clear_all(cls):
        """清理所有单例实例"""
        cls._instances.clear()
        cls._logger.info("🧹 清理所有单例实例")
    
    @classmethod
    def get_instance_count(cls) -> int:
        """获取当前单例实例数量"""
        return len(cls._instances)
    
    @classmethod
    def get_instance_names(cls) -> list:
        """获取当前单例实例名称列表"""
        return list(cls._instances.keys())
    
    @classmethod
    def _load_proxy_config(cls) -> Optional[Dict[str, str]]:
        """从配置文件加载代理设置"""
        try:
            config_path = "config/config.json"
            if not os.path.exists(config_path):
                cls._logger.warning(f"配置文件不存在: {config_path}")
                return None
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 优先使用 binance.proxies，如果没有则使用全局 proxies
            proxies = config.get('binance', {}).get('proxies')
            if not proxies:
                proxies = config.get('proxies')
            
            # 检查代理配置是否为空
            if not proxies or proxies == {}:
                cls._logger.info("🔧 配置文件中未设置代理")
                return None
            
            cls._logger.info(f"🔧 从配置文件加载代理设置: {proxies}")
            return proxies
            
        except Exception as e:
            cls._logger.error(f"加载代理配置失败: {e}")
            return None
    
    def initialize(self) -> bool:
        """初始化单例管理器"""
        try:
            self._initialized = True
            self._logger.info("单例管理器初始化成功")
            return True
        except Exception as e:
            self._logger.error(f"单例管理器初始化失败: {e}")
            return False
    
    def cleanup(self) -> bool:
        """清理单例管理器资源"""
        try:
            self.clear_all()
            self._initialized = False
            self._logger.info("单例管理器清理完成")
            return True
        except Exception as e:
            self._logger.error(f"单例管理器清理失败: {e}")
            return False
    
    def get_instance(self, cls: type, *args, **kwargs):
        """获取单例实例"""
        class_name = cls.__name__
        if class_name not in self._instances:
            self._instances[class_name] = cls(*args, **kwargs)
            self._logger.info(f"创建单例实例: {class_name}")
        return self._instances[class_name]
    
    def clear_instance(self, cls: type):
        """清除单例实例"""
        class_name = cls.__name__
        if class_name in self._instances:
            del self._instances[class_name]
            self._logger.info(f"清除单例实例: {class_name}")
            return True
        return False


# 便捷函数
def get_binance_provider(enable_futures: bool = False):
    """获取币安数据提供者单例"""
    return SingletonManager.get_binance_provider(enable_futures=enable_futures)


def get_technical_analyzer():
    """获取技术分析器单例"""
    return SingletonManager.get_technical_analyzer()


def get_support_resistance_storage():
    """获取支撑阻力位存储单例"""
    return SingletonManager.get_support_resistance_storage()


# 全局单例管理器实例
singleton_manager = SingletonManager()
