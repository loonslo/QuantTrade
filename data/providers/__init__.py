"""
数据提供者模块
提供统一的数据源访问接口
"""

# 基础接口和类
from .provider_base import (
    IDataProvider,
    BaseDataProvider,
    CachedDataProvider,
    CompositeDataProvider,
    data_provider_context
)

# 具体实现
from .binance_provider import BinanceDataProvider
from .database_provider import DatabaseDataProvider
from .csv_provider import CSVDataProvider
from .finnhub_provider import FinnhubProvider, get_finnhub_provider
from .alpha_vantage_provider import AlphaVantageProvider, get_alpha_vantage_provider

__all__ = [
    # 基础接口和类
    'IDataProvider',
    'BaseDataProvider',
    'CachedDataProvider',
    'CompositeDataProvider',
    'data_provider_context',
    
    # 具体实现
    'BinanceDataProvider',
    'DatabaseDataProvider',
    'CSVDataProvider',
    'FinnhubProvider',
    'AlphaVantageProvider',
    'get_finnhub_provider',
    'get_alpha_vantage_provider',
]


# 数据提供者工厂
class DataProviderFactory:
    """数据提供者工厂"""
    
    _providers = {}
    
    @classmethod
    def create_provider(cls, provider_type: str, **kwargs) -> BaseDataProvider:
        """创建数据提供者实例"""
        if provider_type.lower() == 'binance':
            return BinanceDataProvider(**kwargs)
        elif provider_type.lower() == 'database':
            return DatabaseDataProvider(**kwargs)
        elif provider_type.lower() == 'csv':
            return CSVDataProvider(**kwargs)
        else:
            raise ValueError(f"不支持的数据提供者类型: {provider_type}")
    
    @classmethod
    def get_cached_provider(cls, provider_type: str, **kwargs) -> CachedDataProvider:
        """获取带缓存的数据提供者"""
        cache_key = f"{provider_type}_{hash(str(sorted(kwargs.items())))}"
        
        if cache_key not in cls._providers:
            base_provider = cls.create_provider(provider_type, **kwargs)
            cls._providers[cache_key] = CachedDataProvider(base_provider)
        
        return cls._providers[cache_key]
    
    @classmethod
    def create_composite_provider(cls, provider_configs: list) -> CompositeDataProvider:
        """创建复合数据提供者"""
        providers = []
        
        for config in provider_configs:
            provider_type = config.pop('type')
            provider = cls.create_provider(provider_type, **config)
            providers.append(provider)
        
        return CompositeDataProvider(providers)
    
    @classmethod
    def clear_cache(cls):
        """清除所有缓存的提供者"""
        cls._providers.clear()


# 便捷函数
def get_provider(provider_type: str, **kwargs) -> BaseDataProvider:
    """获取数据提供者实例"""
    return DataProviderFactory.create_provider(provider_type, **kwargs)


def get_cached_provider(provider_type: str, **kwargs) -> CachedDataProvider:
    """获取带缓存的数据提供者实例"""
    return DataProviderFactory.get_cached_provider(provider_type, **kwargs)


def create_multi_source_provider(primary_type: str, 
                                fallback_types: list, 
                                **kwargs) -> CompositeDataProvider:
    """创建多数据源提供者（主要+备用）"""
    configs = [{'type': primary_type, **kwargs}]
    
    for fallback_type in fallback_types:
        configs.append({'type': fallback_type, **kwargs})
    
    return DataProviderFactory.create_composite_provider(configs)