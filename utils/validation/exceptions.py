"""
异常处理模块
提供统一的异常管理，包括自定义异常类和异常处理工具
"""

from typing import Optional, Dict, Any


class QuantTradeException(Exception):
    """量化交易系统基础异常类"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        初始化异常
        
        Args:
            message: 异常消息
            error_code: 错误代码
            details: 详细信息
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self):
        """字符串表示"""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class BacktestException(QuantTradeException):
    """回测异常基类"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        初始化异常
        
        Args:
            message: 异常消息
            error_code: 错误代码
            details: 详细信息
        """
        super().__init__(message, error_code, details)


class DataException(BacktestException):
    """数据异常"""
    
    def __init__(self, message: str, symbol: Optional[str] = None, 
                 timeframe: Optional[str] = None):
        """
        初始化数据异常
        
        Args:
            message: 异常消息
            symbol: 交易对
            timeframe: 时间周期
        """
        super().__init__(message, "DATA_ERROR")
        self.symbol = symbol
        self.timeframe = timeframe


class StrategyException(BacktestException):
    """策略异常"""
    
    def __init__(self, message: str, strategy_name: Optional[str] = None):
        """
        初始化策略异常
        
        Args:
            message: 异常消息
            strategy_name: 策略名称
        """
        super().__init__(message, "STRATEGY_ERROR")
        self.strategy_name = strategy_name


class PositionException(BacktestException):
    """仓位管理异常"""
    
    def __init__(self, message: str, position_type: Optional[str] = None):
        """
        初始化仓位管理异常
        
        Args:
            message: 异常消息
            position_type: 仓位管理类型
        """
        super().__init__(message, "POSITION_ERROR")
        self.position_type = position_type


class RiskException(BacktestException):
    """风险异常"""
    
    def __init__(self, message: str, risk_type: Optional[str] = None):
        """
        初始化风险异常
        
        Args:
            message: 异常消息
            risk_type: 风险类型
        """
        super().__init__(message, "RISK_ERROR")
        self.risk_type = risk_type


class PortfolioException(BacktestException):
    """投资组合异常"""
    
    def __init__(self, message: str, portfolio_id: Optional[str] = None):
        """
        初始化投资组合异常
        
        Args:
            message: 异常消息
            portfolio_id: 投资组合ID
        """
        super().__init__(message, "PORTFOLIO_ERROR")
        self.portfolio_id = portfolio_id


class ConfigurationException(BacktestException):
    """配置异常"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        """
        初始化配置异常
        
        Args:
            message: 异常消息
            config_key: 配置键
        """
        super().__init__(message, "CONFIG_ERROR")
        self.config_key = config_key


class ValidationException(BacktestException):
    """验证异常"""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 value: Optional[Any] = None):
        """
        初始化验证异常
        
        Args:
            message: 异常消息
            field: 字段名
            value: 字段值
        """
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.value = value


class NetworkException(BacktestException):
    """网络异常"""
    
    def __init__(self, message: str, url: Optional[str] = None, 
                 status_code: Optional[int] = None):
        """
        初始化网络异常
        
        Args:
            message: 异常消息
            url: 请求URL
            status_code: 状态码
        """
        super().__init__(message, "NETWORK_ERROR")
        self.url = url
        self.status_code = status_code


class AnalysisException(BacktestException):
    """分析异常"""
    
    def __init__(self, message: str, analysis_type: Optional[str] = None,
                 metric: Optional[str] = None):
        """
        初始化分析异常
        
        Args:
            message: 异常消息
            analysis_type: 分析类型
            metric: 指标名称
        """
        super().__init__(message, "ANALYSIS_ERROR")
        self.analysis_type = analysis_type
        self.metric = metric
    
    def __str__(self):
        """字符串表示"""
        if self.analysis_type:
            return f"[{self.error_code}] {self.message} - Type: {self.analysis_type}"
        return super().__str__()


# 异常处理工具函数
def handle_exception(func):
    """
    异常处理装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BacktestException as e:
            # 记录自定义异常
            print(f"❌ {e}")
            raise
        except Exception as e:
            # 将其他异常转换为BacktestException
            raise BacktestException(f"未处理的异常: {str(e)}", "UNKNOWN_ERROR")
    
    return wrapper


def safe_execute(func, *args, **kwargs):
    """
    安全执行函数
    
    Args:
        func: 要执行的函数
        *args: 位置参数
        **kwargs: 关键字参数
        
    Returns:
        函数执行结果或None（如果发生异常）
    """
    try:
        return func(*args, **kwargs)
    except BacktestException as e:
        print(f"❌ {e}")
        return None
    except Exception as e:
        print(f"❌ 未处理的异常: {str(e)}")
        return None


def validate_not_none(value: Any, name: str):
    """
    验证值不为None
    
    Args:
        value: 要验证的值
        name: 值名称
        
    Raises:
        ValidationException: 如果值为None
    """
    if value is None:
        raise ValidationException(f"{name} 不能为None", name, value)


def validate_positive(value: float, name: str):
    """
    验证值为正数
    
    Args:
        value: 要验证的值
        name: 值名称
        
    Raises:
        ValidationException: 如果值不是正数
    """
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValidationException(f"{name} 必须是正数", name, value)


def validate_range(value: float, min_val: float, max_val: float, name: str):
    """
    验证值在指定范围内
    
    Args:
        value: 要验证的值
        min_val: 最小值
        max_val: 最大值
        name: 值名称
        
    Raises:
        ValidationException: 如果值不在范围内
    """
    if not isinstance(value, (int, float)) or value < min_val or value > max_val:
        raise ValidationException(f"{name} 必须在 {min_val} 和 {max_val} 之间", name, value) 