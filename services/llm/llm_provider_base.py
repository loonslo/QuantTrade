# -*- coding: utf-8 -*-
"""
LLM服务提供者基类
定义所有LLM服务提供者应实现的接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseLLMProvider(ABC):
    """LLM服务提供者基类"""

    def __init__(self, config: Dict[str, Any]):
        """初始化LLM提供者"""
        self.config = config
        self.logger = logger

    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """生成响应"""
        pass

    @abstractmethod
    async def generate_stream_response(self, prompt: str, **kwargs):
        """生成流式响应"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass

    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """获取提供者信息"""
        pass

    def validate_config(self) -> bool:
        """验证配置"""
        required_fields = self.get_required_config_fields()
        for field in required_fields:
            if field not in self.config:
                self.logger.error(f"缺少必需配置字段: {field}")
                return False
        return True

    @abstractmethod
    def get_required_config_fields(self) -> list:
        """获取必需配置字段"""
        pass

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新配置"""
        self.config.update(new_config)
        self.logger.info("配置已更新")

    def log_request(self, prompt: str, **kwargs) -> None:
        """记录请求日志"""
        self.logger.debug(f"LLM请求: {prompt[:100]}...")

    def log_response(self, response: str) -> None:
        """记录响应日志"""
        self.logger.debug(f"LLM响应: {response[:100]}...")

    def log_error(self, error: Exception) -> None:
        """记录错误日志"""
        self.logger.error(f"LLM错误: {error}")

    def format_prompt(self, prompt: str, **kwargs) -> str:
        """格式化提示"""
        # 可以在这里添加通用的提示格式化逻辑
        return prompt

    def validate_prompt(self, prompt: str) -> bool:
        """验证提示"""
        if not prompt or not prompt.strip():
            self.logger.error("提示不能为空")
            return False
        return True

    def get_max_tokens(self) -> int:
        """获取最大token数"""
        return self.get_config_value('max_tokens', 4096)

    def get_temperature(self) -> float:
        """获取温度参数"""
        return self.get_config_value('temperature', 0.7)

    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.get_config_value('model', 'default')

    def is_streaming_enabled(self) -> bool:
        """是否启用流式响应"""
        return self.get_config_value('streaming', False)

    def get_timeout(self) -> int:
        """获取超时时间"""
        return self.get_config_value('timeout', 30)

    def get_retry_count(self) -> int:
        """获取重试次数"""
        return self.get_config_value('retry_count', 3)

    def get_retry_delay(self) -> float:
        """获取重试延迟"""
        return self.get_config_value('retry_delay', 1.0)

    def should_retry(self, error: Exception) -> bool:
        """是否应该重试"""
        # 可以在这里定义重试条件
        return True

    def get_error_message(self, error: Exception) -> str:
        """获取错误消息"""
        return str(error)

    def cleanup(self) -> None:
        """清理资源"""
        pass

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()