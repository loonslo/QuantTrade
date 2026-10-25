"""
装饰器模块
提供异常处理、安全执行和输入验证的装饰器
"""

import functools
import time
from typing import Any, Callable, Dict, Optional
from datetime import datetime

from ..core.logger_manager import get_logger
from .exceptions import (
    BacktestException, DataException, StrategyException,
    ValidationException, ConfigurationException
)


def handle_exception(func: Callable) -> Callable:
    """
    异常处理装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BacktestException as e:
            # 记录自定义异常
            logger = get_logger(f"{func.__module__}.{func.__name__}")
            logger.error(f"❌ {e}")
            raise
        except Exception as e:
            # 将其他异常转换为BacktestException
            logger = get_logger(f"{func.__module__}.{func.__name__}")
            logger.error(f"❌ 未处理的异常: {str(e)}")
            raise BacktestException(f"未处理的异常: {str(e)}", "UNKNOWN_ERROR")
    
    return wrapper


def safe_execute(default_return: Any = None, 
                 log_errors: bool = True) -> Callable:
    """
    安全执行装饰器
    
    Args:
        default_return: 发生异常时的默认返回值
        log_errors: 是否记录错误日志
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BacktestException as e:
                if log_errors:
                    logger = get_logger(f"{func.__module__}.{func.__name__}")
                    logger.error(f"❌ {e}")
                return default_return
            except Exception as e:
                if log_errors:
                    logger = get_logger(f"{func.__module__}.{func.__name__}")
                    logger.error(f"❌ 未处理的异常: {str(e)}")
                return default_return
        return wrapper
    return decorator


def validate_input(validation_rules: Dict[str, Any]) -> Callable:
    """
    输入验证装饰器
    
    Args:
        validation_rules: 验证规则字典
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 合并位置参数和关键字参数
            func_args = func.__code__.co_varnames[:func.__code__.co_argcount]
            all_args = dict(zip(func_args, args))
            all_args.update(kwargs)
            
            # 执行验证
            for param_name, rules in validation_rules.items():
                if param_name in all_args:
                    value = all_args[param_name]
                    validate_parameter(param_name, value, rules)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def retry(max_attempts: int = 3, 
          delay: float = 1.0,
          backoff_factor: float = 2.0,
          exceptions: tuple = (Exception,)) -> Callable:
    """
    重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 退避因子
        exceptions: 需要重试的异常类型
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger = get_logger(f"{func.__module__}.{func.__name__}")
                        logger.warning(f"第 {attempt + 1} 次尝试失败: {e}, {current_delay}秒后重试")
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger = get_logger(f"{func.__module__}.{func.__name__}")
                        logger.error(f"重试 {max_attempts} 次后仍然失败: {e}")
            
            raise last_exception
        return wrapper
    return decorator


def cache_result(ttl: Optional[int] = None, 
                max_size: int = 100) -> Callable:
    """
    结果缓存装饰器
    
    Args:
        ttl: 缓存生存时间（秒），None表示永不过期
        max_size: 最大缓存条目数
        
    Returns:
        装饰器函数
    """
    cache = {}
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = str((func.__name__, args, tuple(sorted(kwargs.items()))))
            
            # 检查缓存
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if ttl is None or (datetime.now().timestamp() - timestamp) < ttl:
                    return result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            if len(cache) >= max_size:
                # 移除最旧的条目
                oldest_key = min(cache.keys(), key=lambda k: cache[k][1])
                del cache[oldest_key]
            
            cache[cache_key] = (result, datetime.now().timestamp())
            return result
        return wrapper
    return decorator


def performance_monitor(func: Callable) -> Callable:
    """
    性能监控装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = get_memory_usage()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            end_memory = get_memory_usage()
            
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            
            logger = get_logger(f"{func.__module__}.{func.__name__}")
            logger.info(f"执行时间: {execution_time:.4f}秒, 内存使用: {memory_usage:.2f}MB")
    
    return wrapper


def validate_parameter(param_name: str, value: Any, rules: Dict[str, Any]) -> None:
    """
    验证单个参数
    
    Args:
        param_name: 参数名称
        value: 参数值
        rules: 验证规则
        
    Raises:
        ValidationException: 验证失败时抛出
    """
    # 类型验证
    if 'type' in rules:
        expected_type = rules['type']
        if not isinstance(value, expected_type):
            raise ValidationException(
                f"参数 {param_name} 类型错误: 期望 {expected_type.__name__}, 实际 {type(value).__name__}",
                param_name, value
            )
    
    # 范围验证
    if 'min' in rules and value < rules['min']:
        raise ValidationException(
            f"参数 {param_name} 值过小: {value} < {rules['min']}",
            param_name, value
        )
    
    if 'max' in rules and value > rules['max']:
        raise ValidationException(
            f"参数 {param_name} 值过大: {value} > {rules['max']}",
            param_name, value
        )
    
    # 长度验证
    if 'min_length' in rules and len(value) < rules['min_length']:
        raise ValidationException(
            f"参数 {param_name} 长度过短: {len(value)} < {rules['min_length']}",
            param_name, value
        )
    
    if 'max_length' in rules and len(value) > rules['max_length']:
        raise ValidationException(
            f"参数 {param_name} 长度过长: {len(value)} > {rules['max_length']}",
            param_name, value
        )
    
    # 枚举验证
    if 'choices' in rules and value not in rules['choices']:
        raise ValidationException(
            f"参数 {param_name} 值无效: {value} not in {rules['choices']}",
            param_name, value
        )
    
    # 正则表达式验证
    if 'pattern' in rules:
        import re
        if not re.match(rules['pattern'], str(value)):
            raise ValidationException(
                f"参数 {param_name} 格式错误: {value} 不匹配模式 {rules['pattern']}",
                param_name, value
            )


def get_memory_usage() -> float:
    """
    获取当前内存使用量（MB）
    
    Returns:
        内存使用量（MB）
    """
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


# 预定义的验证规则
VALIDATION_RULES = {
    'positive_float': {'type': (int, float), 'min': 0},
    'positive_int': {'type': int, 'min': 0},
    'percentage': {'type': (int, float), 'min': 0, 'max': 1},
    'symbol': {'type': str, 'min_length': 1, 'max_length': 20},
    'timeframe': {'type': str, 'choices': ['1m', '5m', '15m', '30m', '1h', '4h', '1d']},
    'action': {'type': str, 'choices': ['buy', 'sell', 'hold']}
} 