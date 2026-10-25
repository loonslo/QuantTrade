"""
工具接口定义
定义各种工具类的统一接口和基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass


@dataclass
class ToolConfig:
    """工具配置基类"""
    name: str
    version: str = "1.0.0"
    enabled: bool = True
    config: Dict[str, Any] = None


class BaseTool(ABC):
    """工具基类"""
    
    def __init__(self, config: ToolConfig):
        self.config = config
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化工具"""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """清理资源"""
        pass
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    def get_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        return {
            "name": self.config.name,
            "version": self.config.version,
            "enabled": self.config.enabled,
            "initialized": self._initialized
        }


class ConfigManagerInterface(BaseTool):
    """配置管理器接口"""
    
    @abstractmethod
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """加载配置"""
        pass
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        pass
    
    @abstractmethod
    def reload(self) -> bool:
        """重新加载配置"""
        pass


class LoggerManagerInterface(BaseTool):
    """日志管理器接口"""
    
    @abstractmethod
    def get_logger(self, name: str):
        """获取日志器"""
        pass
    
    @abstractmethod
    def setup_logger(self, name: str, config: Optional[Dict[str, Any]] = None):
        """设置日志器"""
        pass


class SingletonManagerInterface(BaseTool):
    """单例管理器接口"""
    
    @abstractmethod
    def get_instance(self, cls: type, *args, **kwargs):
        """获取单例实例"""
        pass
    
    @abstractmethod
    def clear_instance(self, cls: type):
        """清除单例实例"""
        pass


class ValidationInterface(BaseTool):
    """验证工具接口"""
    
    @abstractmethod
    def validate(self, data: Any, schema: Any) -> bool:
        """验证数据"""
        pass
    
    @abstractmethod
    def get_errors(self) -> List[str]:
        """获取验证错误"""
        pass


class TimeInterface(BaseTool):
    """时间工具接口"""
    
    @abstractmethod
    def get_current_time(self) -> str:
        """获取当前时间"""
        pass
    
    @abstractmethod
    def format_time(self, timestamp: Any, format_str: str) -> str:
        """格式化时间"""
        pass


class HelperInterface(BaseTool):
    """助手工具接口"""
    
    @abstractmethod
    def process_data(self, data: Any) -> Any:
        """处理数据"""
        pass
    
    @abstractmethod
    def format_output(self, data: Any) -> str:
        """格式化输出"""
        pass


class ServiceInterface(BaseTool):
    """服务工具接口"""
    
    @abstractmethod
    def start_service(self) -> bool:
        """启动服务"""
        pass
    
    @abstractmethod
    def stop_service(self) -> bool:
        """停止服务"""
        pass
    
    @abstractmethod
    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        pass
