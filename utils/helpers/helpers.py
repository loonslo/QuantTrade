"""
辅助函数模块
提供常用的工具函数
"""

import os
import re
import locale
from pathlib import Path
from typing import Any, List, Optional, Union, Dict
from datetime import datetime
from functools import wraps
import time

from ..core.logger_manager import get_logger


def format_number(value: Union[int, float], 
                 decimal_places: int = 2,
                 thousands_separator: bool = True) -> str:
    """
    格式化数字
    
    Args:
        value: 要格式化的数值
        decimal_places: 小数位数
        thousands_separator: 是否使用千位分隔符
        
    Returns:
        格式化后的字符串
    """
    try:
        if thousands_separator:
            return f"{value:,.{decimal_places}f}"
        else:
            return f"{value:.{decimal_places}f}"
    except (ValueError, TypeError):
        return str(value)


def format_percentage(value: float, 
                     decimal_places: int = 2,
                     include_sign: bool = True) -> str:
    """
    格式化百分比
    
    Args:
        value: 要格式化的数值（0-1之间）
        decimal_places: 小数位数
        include_sign: 是否包含正负号
        
    Returns:
        格式化后的百分比字符串
    """
    try:
        percentage = value * 100
        if include_sign and percentage > 0:
            return f"+{percentage:.{decimal_places}f}%"
        else:
            return f"{percentage:.{decimal_places}f}%"
    except (ValueError, TypeError):
        return str(value)


def format_currency(value: float,
                   currency: str = "USD",
                   decimal_places: int = 2) -> str:
    """
    格式化货币
    
    Args:
        value: 要格式化的数值
        currency: 货币代码
        decimal_places: 小数位数
        
    Returns:
        格式化后的货币字符串
    """
    try:
        currency_symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "CNY": "¥",
            "JPY": "¥"
        }
        
        symbol = currency_symbols.get(currency, currency)
        return f"{symbol}{value:,.{decimal_places}f}"
    except (ValueError, TypeError):
        return str(value)


def calculate_percentage(part: float, total: float) -> float:
    """
    计算百分比
    
    Args:
        part: 部分值
        total: 总值
        
    Returns:
        百分比值（0-1之间）
    """
    if total == 0:
        return 0.0
    return part / total


def validate_date_range(start_date: Union[str, datetime],
                       end_date: Union[str, datetime]) -> bool:
    """
    验证日期范围
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        是否有效
    """
    try:
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        return start_date < end_date
    except (ValueError, TypeError):
        return False


def generate_timestamp(prefix: str = "",
                      suffix: str = "",
                      format_str: str = "%Y%m%d_%H%M%S") -> str:
    """
    生成时间戳
    
    Args:
        prefix: 前缀
        suffix: 后缀
        format_str: 时间格式
        
    Returns:
        时间戳字符串
    """
    timestamp = datetime.now().strftime(format_str)
    return f"{prefix}{timestamp}{suffix}"


def create_directory(path: Union[str, Path], 
                    exist_ok: bool = True) -> Path:
    """
    创建目录
    
    Args:
        path: 目录路径
        exist_ok: 如果目录已存在是否不报错
        
    Returns:
        创建的目录路径
    """
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=exist_ok)
    return directory


def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除前后空格
    filename = filename.strip()
    # 确保不为空
    if not filename:
        filename = "unnamed"
    return filename


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    获取文件大小（字节）
    
    Args:
        file_path: 文件路径
        
    Returns:
        文件大小（字节）
    """
    try:
        return Path(file_path).stat().st_size
    except (OSError, FileNotFoundError):
        return 0


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化后的文件大小字符串
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"


def is_valid_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        是否有效
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_url(url: str) -> bool:
    """
    验证URL格式
    
    Args:
        url: URL地址
        
    Returns:
        是否有效
    """
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
    return bool(re.match(pattern, url))


def extract_numbers(text: str) -> List[float]:
    """
    从文本中提取数字
    
    Args:
        text: 输入文本
        
    Returns:
        提取的数字列表
    """
    pattern = r'-?\d*\.?\d+'
    numbers = re.findall(pattern, text)
    return [float(num) for num in numbers]


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分块
    
    Args:
        lst: 输入列表
        chunk_size: 块大小
        
    Returns:
        分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(nested_list: List[Any]) -> List[Any]:
    """
    扁平化嵌套列表
    
    Args:
        nested_list: 嵌套列表
        
    Returns:
        扁平化后的列表
    """
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def remove_duplicates(lst: List[Any], preserve_order: bool = True) -> List[Any]:
    """
    移除列表中的重复项
    
    Args:
        lst: 输入列表
        preserve_order: 是否保持原有顺序
        
    Returns:
        去重后的列表
    """
    if preserve_order:
        seen = set()
        result = []
        for item in lst:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
    else:
        return list(set(lst))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    安全除法
    
    Args:
        numerator: 分子
        denominator: 分母
        default: 除零时的默认值
        
    Returns:
        除法结果
    """
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ValueError):
        return default


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    限制数值在指定范围内
    
    Args:
        value: 输入值
        min_val: 最小值
        max_val: 最大值
        
    Returns:
        限制后的值
    """
    return max(min_val, min(value, max_val))


def round_to_significant_digits(value: float, significant_digits: int) -> float:
    """
    四舍五入到指定有效数字
    
    Args:
        value: 输入值
        significant_digits: 有效数字位数
        
    Returns:
        四舍五入后的值
    """
    if value == 0:
        return 0.0
    
    # 计算有效数字的位数
    magnitude = int(abs(value))
    if magnitude == 0:
        magnitude = 1
    
    # 计算需要的小数位数
    decimal_places = significant_digits - len(str(magnitude))
    
    return round(value, decimal_places)


def get_system_locale() -> str:
    """
    获取系统区域设置
    
    Returns:
        区域设置字符串
    """
    try:
        return locale.getlocale()[0] or 'en_US'
    except (AttributeError, ValueError):
        return 'en_US'


def is_windows() -> bool:
    """
    检查是否为Windows系统
    
    Returns:
        是否为Windows
    """
    return os.name == 'nt'


def is_linux() -> bool:
    """
    检查是否为Linux系统
    
    Returns:
        是否为Linux
    """
    return os.name == 'posix' and 'linux' in os.uname().sysname.lower()


def is_macos() -> bool:
    """
    检查是否为macOS系统
    
    Returns:
        是否为macOS
    """
    return os.name == 'posix' and 'darwin' in os.uname().sysname.lower()


def get_available_memory() -> Optional[int]:
    """
    获取可用内存（字节）
    
    Returns:
        可用内存字节数，如果无法获取则返回None
    """
    try:
        import psutil
        return psutil.virtual_memory().available
    except ImportError:
        return None


def get_cpu_count() -> int:
    """
    获取CPU核心数
    
    Returns:
        CPU核心数
    """
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except (ImportError, NotImplementedError):
        return 1


# 性能监控装饰器
def performance_monitor(func_name: Optional[str] = None):
    """
    性能监控装饰器
    
    Args:
        func_name: 自定义函数名，用于日志记录
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger('performance')
            name = func_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"{name} 执行时间: {execution_time:.4f}秒")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{name} 执行失败 (耗时: {execution_time:.4f}秒): {e}")
                raise
        
        return wrapper
    return decorator


# 重试装饰器
def retry_on_exception(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    异常重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间倍数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger('retry')
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} 重试 {max_attempts} 次后仍然失败: {e}")
                        raise
                    
                    logger.warning(f"{func.__name__} 第 {attempt + 1} 次尝试失败: {e}, {current_delay}秒后重试")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
        return wrapper
    return decorator


# 数据验证工具
def validate_numeric_range(value: Union[int, float], 
                          min_val: Optional[Union[int, float]] = None,
                          max_val: Optional[Union[int, float]] = None,
                          name: str = "value") -> bool:
    """
    验证数值范围
    
    Args:
        value: 要验证的数值
        min_val: 最小值
        max_val: 最大值
        name: 参数名称，用于错误信息
        
    Returns:
        bool: 是否在有效范围内
        
    Raises:
        ValueError: 数值超出范围
    """
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} 必须是数值类型")
    
    if min_val is not None and value < min_val:
        raise ValueError(f"{name} 不能小于 {min_val}")
    
    if max_val is not None and value > max_val:
        raise ValueError(f"{name} 不能大于 {max_val}")
    
    return True


def safe_divide(numerator: Union[int, float], 
                denominator: Union[int, float], 
                default: Union[int, float] = 0.0) -> Union[int, float]:
    """
    安全除法，避免除零错误
    
    Args:
        numerator: 分子
        denominator: 分母
        default: 除零时的默认值
        
    Returns:
        除法结果或默认值
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError):
        return default


# 文件操作工具
def ensure_directory(path: Union[str, Path]) -> Path:
    """
    确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        Path: 目录路径对象
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    获取文件大小（字节）
    
    Args:
        file_path: 文件路径
        
    Returns:
        int: 文件大小，文件不存在时返回0
    """
    try:
        return Path(file_path).stat().st_size
    except (OSError, FileNotFoundError):
        return 0


# 字符串处理工具
def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    截断字符串
    
    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        str: 截断后的字符串
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def clean_filename(filename: str) -> str:
    """
    清理文件名，移除非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    # 移除或替换非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    cleaned = re.sub(illegal_chars, '_', filename)
    
    # 移除多余的空格和点
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = cleaned.strip('.')
    
    return cleaned or "unnamed"


# 配置工具
def load_config_from_env(prefix: str = "") -> Dict[str, Any]:
    """
    从环境变量加载配置
    
    Args:
        prefix: 环境变量前缀
        
    Returns:
        Dict[str, Any]: 配置字典
    """
    import os
    config = {}
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            config_key = key[len(prefix):].lower()
            
            # 尝试转换数据类型
            if value.lower() in ('true', 'false'):
                config[config_key] = value.lower() == 'true'
            elif value.isdigit():
                config[config_key] = int(value)
            elif value.replace('.', '').isdigit():
                config[config_key] = float(value)
            else:
                config[config_key] = value
    
    return config 