"""
基础数据提供者
定义统一的数据提供者接口和通用功能
"""

import pandas as pd
from typing import Dict, Any, Optional, List, Union, Protocol, runtime_checkable
from datetime import datetime
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
import asyncio
import time

from utils.core.logger_manager import get_logger
from utils.validation.exceptions import DataException, ValidationException


@runtime_checkable
class IDataProvider(Protocol):
    """数据提供者接口协议"""
    
    def get_ohlcv(self, 
                  symbol: str, 
                  timeframe: str = '1m',
                  start_time: Optional[Union[datetime, int]] = None,
                  end_time: Optional[Union[datetime, int]] = None,
                  limit: Optional[int] = None) -> pd.DataFrame:
        """获取OHLCV数据"""
        ...
    
    def get_symbols(self) -> List[str]:
        """获取可用交易对列表"""
        ...
    
    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """获取市场信息"""
        ...


class BaseDataProvider(ABC):
    """基础数据提供者抽象类"""
    
    def __init__(self, provider_name: str = None):
        self.provider_name = provider_name or self.__class__.__name__
        self.logger = get_logger(f"data_provider.{self.provider_name.lower()}")
        self._cache = {}
        self._cache_ttl = {}
        self.default_cache_timeout = 300  # 5分钟默认缓存
        
        # 连接状态
        self._connected = False
        self._last_health_check = 0
        self.health_check_interval = 60  # 1分钟健康检查间隔
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 1.0
        self.backoff_factor = 2.0
        
        # 速率限制
        self._last_request_time = 0
        self.rate_limit_delay = 0.1  # 100ms间隔
    
    @abstractmethod
    def get_ohlcv(self, 
                  symbol: str, 
                  timeframe: str = '1m',
                  start_time: Optional[Union[datetime, int]] = None,
                  end_time: Optional[Union[datetime, int]] = None,
                  limit: Optional[int] = None) -> pd.DataFrame:
        """获取OHLCV数据"""
        pass
    
    @abstractmethod
    def get_symbols(self) -> List[str]:
        """获取可用交易对列表"""
        pass
    
    @abstractmethod
    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """获取市场信息"""
        pass
    
    def validate_symbol(self, symbol: str) -> bool:
        """验证交易对格式"""
        if not symbol or not isinstance(symbol, str):
            return False
        
        # 基本格式验证
        if '/' not in symbol:
            return False
        
        parts = symbol.split('/')
        if len(parts) != 2:
            return False
        
        base, quote = parts
        if not base or not quote:
            return False
        
        return True
    
    def validate_timeframe(self, timeframe: str) -> bool:
        """验证时间周期格式"""
        valid_timeframes = [
            '1m', '3m', '5m', '15m', '30m',
            '1h', '2h', '4h', '6h', '8h', '12h',
            '1d', '3d', '1w', '1M'
        ]
        return timeframe in valid_timeframes
    
    def normalize_symbol(self, symbol: str) -> str:
        """标准化交易对格式"""
        if not self.validate_symbol(symbol):
            raise ValidationException(f"无效的交易对格式: {symbol}")
        
        # 转换为大写并确保格式一致
        parts = symbol.upper().split('/')
        return f"{parts[0]}/{parts[1]}"
    
    def convert_timestamp(self, timestamp: Union[datetime, int, float]) -> int:
        """转换时间戳为毫秒级整数"""
        if isinstance(timestamp, datetime):
            return int(timestamp.timestamp() * 1000)
        elif isinstance(timestamp, (int, float)):
            # 假设如果小于1e10则为秒级时间戳，否则为毫秒级
            if timestamp < 1e10:
                return int(timestamp * 1000)
            else:
                return int(timestamp)
        else:
            raise ValidationException(f"不支持的时间戳类型: {type(timestamp)}")
    
    def convert_to_datetime(self, timestamp: Union[datetime, int, float]) -> datetime:
        """转换时间戳为datetime对象"""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, (int, float)):
            # 假设如果小于1e10则为秒级时间戳，否则为毫秒级
            if timestamp < 1e10:
                return datetime.fromtimestamp(timestamp)
            else:
                return datetime.fromtimestamp(timestamp / 1000)
        else:
            raise ValidationException(f"不支持的时间戳类型: {type(timestamp)}")
    
    def retry_operation(self, operation, operation_name: str = "操作"):
        """重试操作装饰器"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # 速率限制控制
                self._apply_rate_limit()
                
                result = operation()
                self._last_request_time = time.time()
                return result
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"第 {attempt + 1} 次尝试 {operation_name} 失败: {e}")
                
                if attempt < self.max_retries - 1:
                    # 指数退避重试
                    delay = self.retry_delay * (self.backoff_factor ** attempt)
                    self.logger.info(f"等待 {delay:.2f} 秒后重试...")
                    time.sleep(delay)
                else:
                    self.logger.error(f"{operation_name} 重试 {self.max_retries} 次后失败")
        
        raise DataException(f"{operation_name} 失败: {last_exception}")
    
    def _apply_rate_limit(self):
        """应用速率限制"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
    
    def cache_get(self, key: str) -> Any:
        """从缓存获取数据"""
        if key in self._cache:
            # 检查是否过期
            if key in self._cache_ttl:
                if time.time() > self._cache_ttl[key]:
                    # 缓存过期，删除
                    del self._cache[key]
                    del self._cache_ttl[key]
                    return None
            return self._cache[key]
        return None
    
    def cache_set(self, key: str, value: Any, ttl: int = None):
        """设置缓存数据"""
        self._cache[key] = value
        if ttl is None:
            ttl = self.default_cache_timeout
        self._cache_ttl[key] = time.time() + ttl
    
    def cache_clear(self, pattern: str = None):
        """清除缓存"""
        if pattern is None:
            self._cache.clear()
            self._cache_ttl.clear()
        else:
            # 模式匹配清除
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]
                if key in self._cache_ttl:
                    del self._cache_ttl[key]
    
    def health_check(self) -> bool:
        """健康检查"""
        current_time = time.time()
        if current_time - self._last_health_check < self.health_check_interval:
            return self._connected
        
        try:
            # 执行简单的连接测试
            self._connected = self._perform_health_check()
            self._last_health_check = current_time
            
            if self._connected:
                self.logger.debug(f"{self.provider_name} 健康检查通过")
            else:
                self.logger.warning(f"{self.provider_name} 健康检查失败")
            
            return self._connected
            
        except Exception as e:
            self.logger.error(f"{self.provider_name} 健康检查异常: {e}")
            self._connected = False
            return False
    
    def _perform_health_check(self) -> bool:
        """执行具体的健康检查逻辑"""
        # 子类可以重写此方法实现具体的健康检查
        try:
            # 默认尝试获取交易对列表作为健康检查
            symbols = self.get_symbols()
            return len(symbols) > 0
        except Exception:
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """获取提供者信息"""
        return {
            'name': self.provider_name,
            'connected': self._connected,
            'last_health_check': self._last_health_check,
            'cache_size': len(self._cache),
            'supported_timeframes': self.get_supported_timeframes(),
            'rate_limit_delay': self.rate_limit_delay,
            'max_retries': self.max_retries
        }
    
    def get_supported_timeframes(self) -> List[str]:
        """获取支持的时间周期"""
        # 默认支持的时间周期，子类可以重写
        return ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
    
    def format_ohlcv_dataframe(self, data: List[List], symbol: str) -> pd.DataFrame:
        """格式化OHLCV数据为标准DataFrame"""
        if not data:
            return pd.DataFrame(columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # 转换时间戳
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['symbol'] = symbol
        
        # 重新排列列顺序
        df = df[['symbol', 'datetime', 'open', 'high', 'low', 'close', 'volume']]
        
        # 设置索引
        df.set_index('datetime', inplace=True)
        
        # 确保数值类型
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    async def get_ohlcv_async(self, 
                            symbol: str, 
                            timeframe: str = '1m',
                            start_time: Optional[Union[datetime, int]] = None,
                            end_time: Optional[Union[datetime, int]] = None,
                            limit: Optional[int] = None) -> pd.DataFrame:
        """异步获取OHLCV数据"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.get_ohlcv, 
            symbol, timeframe, start_time, end_time, limit
        )
    
    async def get_symbols_async(self) -> List[str]:
        """异步获取交易对列表"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_symbols)
    
    async def get_market_info_async(self, symbol: str) -> Dict[str, Any]:
        """异步获取市场信息"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_market_info, symbol)


class CachedDataProvider(BaseDataProvider):
    """带缓存的数据提供者装饰器"""
    
    def __init__(self, provider: IDataProvider, cache_timeout: int = 300):
        super().__init__(f"Cached{provider.__class__.__name__}")
        self.provider = provider
        self.cache_timeout = cache_timeout
    
    def get_ohlcv(self, 
                  symbol: str, 
                  timeframe: str = '1m',
                  start_time: Optional[Union[datetime, int]] = None,
                  end_time: Optional[Union[datetime, int]] = None,
                  limit: Optional[int] = None) -> pd.DataFrame:
        """带缓存的获取OHLCV数据"""
        # 生成缓存键
        cache_key = f"ohlcv:{symbol}:{timeframe}:{start_time}:{end_time}:{limit}"
        
        # 尝试从缓存获取
        cached_data = self.cache_get(cache_key)
        if cached_data is not None:
            self.logger.debug(f"从缓存获取数据: {cache_key}")
            return cached_data
        
        # 从原始提供者获取数据
        data = self.provider.get_ohlcv(symbol, timeframe, start_time, end_time, limit)
        
        # 缓存数据
        self.cache_set(cache_key, data, self.cache_timeout)
        
        return data
    
    def get_symbols(self) -> List[str]:
        """带缓存的获取交易对列表"""
        cache_key = "symbols"
        
        cached_data = self.cache_get(cache_key)
        if cached_data is not None:
            return cached_data
        
        data = self.provider.get_symbols()
        self.cache_set(cache_key, data, self.cache_timeout)
        
        return data
    
    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """带缓存的获取市场信息"""
        cache_key = f"market_info:{symbol}"
        
        cached_data = self.cache_get(cache_key)
        if cached_data is not None:
            return cached_data
        
        data = self.provider.get_market_info(symbol)
        self.cache_set(cache_key, data, self.cache_timeout)
        
        return data


class CompositeDataProvider(BaseDataProvider):
    """复合数据提供者，支持多个数据源的故障转移"""
    
    def __init__(self, providers: List[IDataProvider], provider_name: str = "CompositeProvider"):
        super().__init__(provider_name)
        self.providers = providers
        self.primary_provider_index = 0
    
    def get_ohlcv(self, 
                  symbol: str, 
                  timeframe: str = '1m',
                  start_time: Optional[Union[datetime, int]] = None,
                  end_time: Optional[Union[datetime, int]] = None,
                  limit: Optional[int] = None) -> pd.DataFrame:
        """从多个提供者获取OHLCV数据，支持故障转移"""
        last_exception = None
        
        # 首先尝试主要提供者
        for i, provider in enumerate(self.providers):
            try:
                self.logger.debug(f"尝试从提供者 {i} 获取数据: {provider.__class__.__name__}")
                data = provider.get_ohlcv(symbol, timeframe, start_time, end_time, limit)
                
                if not data.empty:
                    # 更新主要提供者索引
                    self.primary_provider_index = i
                    return data
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"提供者 {i} 获取数据失败: {e}")
                continue
        
        # 所有提供者都失败
        raise DataException(f"所有数据提供者都无法获取数据: {last_exception}")
    
    def get_symbols(self) -> List[str]:
        """从多个提供者获取交易对列表"""
        for i, provider in enumerate(self.providers):
            try:
                symbols = provider.get_symbols()
                if symbols:
                    return symbols
            except Exception as e:
                self.logger.warning(f"提供者 {i} 获取交易对列表失败: {e}")
                continue
        
        raise DataException("所有数据提供者都无法获取交易对列表")
    
    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """从多个提供者获取市场信息"""
        for i, provider in enumerate(self.providers):
            try:
                info = provider.get_market_info(symbol)
                if info:
                    return info
            except Exception as e:
                self.logger.warning(f"提供者 {i} 获取市场信息失败: {e}")
                continue
        
        raise DataException(f"所有数据提供者都无法获取市场信息: {symbol}")


@asynccontextmanager
async def data_provider_context(provider: IDataProvider):
    """数据提供者上下文管理器"""
    try:
        # 执行健康检查
        if hasattr(provider, 'health_check'):
            if not provider.health_check():
                raise DataException(f"数据提供者 {provider.__class__.__name__} 健康检查失败")
        
        yield provider
        
    except Exception as e:
        # 记录错误
        if hasattr(provider, 'logger'):
            provider.logger.error(f"数据提供者操作失败: {e}")
        raise
    
    finally:
        # 清理资源
        if hasattr(provider, 'cleanup'):
            provider.cleanup()