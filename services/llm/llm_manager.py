# -*- coding: utf-8 -*-
"""
LLM管理器
统一管理所有LLM提供者的实例
"""

from typing import Dict, Any, Optional, List
from .llm_provider_base import BaseLLMProvider
from utils.core.logger_manager import get_logger
from .providers import SiliconFlowProvider, SiliconFlowWebProvider

class LLMManager:
    """大模型管理器 - 统一提供者管理"""

    def __init__(self):
        self.logger = get_logger("api.llm_manager")
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider = None
        self._load_config()

    def _load_config(self):
        """加载配置"""
        try:
            from .llm_config import LLMConfig
            llm_config = LLMConfig()

            # 初始化提供者
            # OpenAIProvider 暂未实现
            # if llm_config.openai_enabled:
            #     self.providers["openai"] = OpenAIProvider(
            #         llm_config.openai_api_key,
            #         llm_config.openai_base_url
            #     )
            #     if llm_config.default_provider == "openai":
            #         self.default_provider = "openai"

            # ClaudeProvider 暂未实现
            # if llm_config.claude_enabled:
            #     self.providers["claude"] = ClaudeProvider(llm_config.claude_api_key)
            #     if llm_config.default_provider == "claude":
            #         self.default_provider = "claude"

            # LocalLLMProvider 暂未实现
            # if llm_config.local_enabled:
            #     self.providers["local"] = LocalLLMProvider(
            #         api_key="",  # 本地模型不需要API key
            #         base_url=llm_config.local_base_url,
            #         model_name=llm_config.local_model
            #     )
            #     if llm_config.default_provider == "local":
            #         self.default_provider = "local"

            if llm_config.siliconflow_enabled:
                self.providers["siliconflow"] = SiliconFlowProvider(
                    api_key=llm_config.siliconflow_api_key,
                    base_url=llm_config.siliconflow_base_url
                )
                if llm_config.default_provider == "siliconflow":
                    self.default_provider = "siliconflow"

            # 如果没有设置默认提供者，使用第一个可用的
            if not self.default_provider and self.providers:
                self.default_provider = list(self.providers.keys())[0]

            self.logger.info(f"加载{len(self.providers)} 大模型提供者，默认: {self.default_provider}")

        except Exception as e:
            self.logger.error(f"加载大模型配置失败: {str(e)}")

    def get_provider(self, provider_name: Optional[str] = None) -> Optional[BaseLLMProvider]:
        """获取指定提供者"""
        if provider_name and provider_name in self.providers:
            return self.providers[provider_name]
        elif self.default_provider:
            return self.providers[self.default_provider]
        return None

    def get_available_providers(self) -> List[str]:
        """获取可用提供者列表"""
        return [name for name, provider in self.providers.items()
                if provider.is_service_available()]

    def get_provider_info(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """获取提供者信息"""
        provider = self.providers.get(provider_name)
        if provider:
            return provider.get_model_info()
        return None

    async def test_all_connections(self) -> Dict[str, bool]:
        """测试所有提供者连接"""
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = await provider.test_connection()
            except Exception as e:
                self.logger.error(f"测试 {name} 连接失败: {str(e)}")
                results[name] = False
        return results

    def get_enabled_providers(self) -> List[str]:
        """获取配置中启用的提供者列表"""
        from .llm_config import LLMConfig
        llm_config = LLMConfig()
        enabled = []
        for name in self.providers:
            if llm_config.is_provider_enabled(name):
                enabled.append(name)
        return enabled

    async def close(self):
        """关闭所有提供者"""
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()

# 全局LLM管理器实例
llm_manager = LLMManager()