"""
日志系统模块
提供统一的日志管理功能，支持不同级别的日志记录
"""

import logging
import sys  # 新增
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from .interfaces import LoggerManagerInterface, ToolConfig


@dataclass
class LoggerConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


class BacktestLogger:
    """回测日志器"""
    
    def __init__(self, name: str = 'backtest', level: int = logging.INFO, 
                 log_file: Optional[str] = None):
        """
        初始化日志器
        
        Args:
            name: 日志器名称
            level: 日志级别
            log_file: 日志文件路径
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # 防止日志传播到父级日志器
        self.logger.propagate = False
        
        # 只有在没有处理器时才添加处理器，避免重复添加
        if not self.logger.handlers:
            # 创建格式化器
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            # 控制台处理器 - 使用UTF-8编码
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(formatter)
            try:
                # 尝试设置UTF-8编码
                console_handler.stream.reconfigure(encoding='utf-8')
            except AttributeError:
                # 如果Python版本不支持reconfigure，使用标准输出重定向
                import io
                console_handler.stream = io.TextIOWrapper(
                    sys.stderr.buffer,
                    encoding='utf-8',
                    write_through=True
                )
            self.logger.addHandler(console_handler)
            
            # 文件处理器（如果指定了日志文件）
            if log_file:
                # 确保日志目录存在
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        """记录信息日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """记录警告日志"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """记录错误日志"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """记录调试日志"""
        self.logger.debug(message)
    
    def log_trade(self, trade: Dict[str, Any]):
        """记录交易日志"""
        self.info(f"交易执行: {trade}")
    
    def log_signal(self, signal: Dict[str, Any]):
        """记录信号日志"""
        self.info(f"信号生成: {signal}")
    
    def log_error(self, error: Exception, context: str = ""):
        """记录错误日志"""
        self.error(f"{context}: {str(error)}")
    
    def log_performance(self, metrics: Dict[str, Any]):
        """记录性能指标"""
        self.info(f"性能指标: {metrics}")


class LoggerManager(LoggerManagerInterface):
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        初始化日志管理器
        
        Args:
            log_dir: 日志目录
        """
        # 初始化基类
        config = ToolConfig(
            name="LoggerManager",
            version="1.0.0",
            enabled=True,
            config={"log_dir": log_dir}
        )
        super().__init__(config)
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.loggers: Dict[str, BacktestLogger] = {}
    
    def get_logger(self, name: str) -> BacktestLogger:
        """
        获取日志器
        
        Args:
            name: 日志器名称
            
        Returns:
            BacktestLogger: 日志器实例
        """
        if name not in self.loggers:
            log_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
            self.loggers[name] = BacktestLogger(name, log_file=str(log_file))
        
        return self.loggers[name]
    
    def get_backtest_logger(self) -> BacktestLogger:
        """获取回测日志器"""
        return self.get_logger('backtest')
    
    def get_data_logger(self) -> BacktestLogger:
        """获取数据日志器"""
        return self.get_logger('data')
    
    def get_strategy_logger(self) -> BacktestLogger:
        """获取策略日志器"""
        return self.get_logger('strategy')
    
    def get_risk_logger(self) -> BacktestLogger:
        """获取风险日志器"""
        return self.get_logger('risk')
    
    def initialize(self) -> bool:
        """初始化日志管理器"""
        try:
            # 确保日志目录存在
            self.log_dir.mkdir(exist_ok=True)
            self._initialized = True
            return True
        except Exception as e:
            logging.error(f"日志管理器初始化失败: {e}")
            return False
    
    def cleanup(self) -> bool:
        """清理日志管理器资源"""
        try:
            # 关闭所有日志器
            for logger in self.loggers.values():
                for handler in logger.logger.handlers:
                    handler.close()
                    logger.logger.removeHandler(handler)
            
            self.loggers.clear()
            self._initialized = False
            return True
        except Exception as e:
            logging.error(f"日志管理器清理失败: {e}")
            return False
    
    def setup_logger(self, name: str, config: Optional[Dict[str, Any]] = None):
        """设置日志器"""
        if config is None:
            config = {}
        
        # 创建日志器配置
        logger_config = LoggerConfig(
            level=config.get('level', 'INFO'),
            format=config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            file_path=config.get('file_path'),
            max_bytes=config.get('max_bytes', 10 * 1024 * 1024),
            backup_count=config.get('backup_count', 5)
        )
        
        # 创建日志器
        logger = setup_logger(name, logger_config)
        self.loggers[name] = logger
        return logger


def setup_logger(name: str, config: Optional[LoggerConfig] = None) -> BacktestLogger:
    """
    设置日志器
    
    Args:
        name: 日志器名称
        config: 日志配置
        
    Returns:
        BacktestLogger: 日志器实例
    """
    if config is None:
        config = LoggerConfig()
    
    # 转换日志级别
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    level = level_map.get(config.level.upper(), logging.INFO)
    
    # 创建日志器
    logger = BacktestLogger(name, level, config.file_path)
    return logger


# 全局日志管理器实例
logger_manager = LoggerManager()

# 全局日志器缓存
_logger_cache: Dict[str, BacktestLogger] = {}


def get_logger(name: str) -> BacktestLogger:
    """
    获取日志器的便捷函数
    
    Args:
        name: 日志器名称
        
    Returns:
        BacktestLogger: 日志器实例
    """
    # 使用全局缓存避免重复创建日志器
    if name not in _logger_cache:
        _logger_cache[name] = logger_manager.get_logger(name)
    
    return _logger_cache[name]


def log_trade(trade: Dict[str, Any]):
    """记录交易的便捷函数"""
    logger = get_logger('backtest')
    logger.log_trade(trade)


def log_signal(signal: Dict[str, Any]):
    """记录信号的便捷函数"""
    logger = get_logger('strategy')
    logger.log_signal(signal)


def log_error(error: Exception, context: str = ""):
    """记录错误的便捷函数"""
    logger = get_logger('backtest')
    logger.log_error(error, context) 
