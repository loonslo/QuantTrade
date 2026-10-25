# -*- coding: utf-8 -*-
"""
LLM配置管理
管理大模型API的配置
"""

import os
from typing import Dict, Any
from utils.core.logger_manager import get_logger
from utils.core.config_manager import config_manager

class LLMConfig:
    """LLM配置管理"""

    def __init__(self):
        self.logger = get_logger("api.llm.config")
        self._load_config()

    def _load_config(self):
        """从配置文件中加载配置"""
        try:
            # 获取配置
            config = config_manager.load_config()
            llm_config = config.get("llm", {})

            # 提供者配置
            providers_config = llm_config.get("providers", {})

            # OpenAI配置
            openai_config = providers_config.get("openai", {})
            self.openai_api_key = openai_config.get("api_key", "")
            self.openai_base_url = openai_config.get("base_url", "https://api.openai.com/v1")
            self.openai_enabled = openai_config.get("enabled", False) and bool(self.openai_api_key)

            # Claude配置
            claude_config = providers_config.get("claude", {})
            self.claude_api_key = claude_config.get("api_key", "")
            self.claude_enabled = claude_config.get("enabled", False) and bool(self.claude_api_key)

            # SiliconFlow配置（API Key 优先从环境变量读取，不提交到git）
            sf_config = providers_config.get("siliconflow", {})
            env_sf_key = os.getenv("SILICONFLOW_API_KEY", "")
            self.siliconflow_api_key = env_sf_key or sf_config.get("api_key", "") or ""
            self.siliconflow_base_url = sf_config.get("base_url", "https://api.siliconflow.cn")
            self.siliconflow_default_model = sf_config.get("default_model", "Qwen/QwQ-32B")
            self.siliconflow_enabled = sf_config.get("enabled", False) and bool(self.siliconflow_api_key)

            # 本地模型配置
            local_config = providers_config.get("local", {})
            self.local_base_url = local_config.get("base_url", "http://localhost:11434")
            self.local_model = local_config.get("model", "llama2")
            self.local_enabled = local_config.get("enabled", False)

            # 默认提供者
            self.default_provider = llm_config.get("default_provider", "siliconflow")

            # 模型默认参数
            default_params = llm_config.get("default_parameters", {})
            self.default_temperature = float(default_params.get("temperature", 0.7))
            self.default_max_tokens = int(default_params.get("max_tokens", 2000))
            self.default_top_p = float(default_params.get("top_p", 0.9))

            # 超时配置
            timeout_config = llm_config.get("timeout_config", {})
            self.request_timeout = int(timeout_config.get("request_timeout", 30))
            self.max_retries = int(timeout_config.get("max_retries", 3))
            self.retry_delay = float(timeout_config.get("retry_delay", 1.0))

            self.logger.info(f"LLM配置加载完成，默认提供者: {self.default_provider}")

        except Exception as e:
            self.logger.error(f"加载LLM配置失败: {str(e)}")
            # 使用默认配置
            self._load_default_config()

    def _load_default_config(self):
        """加载默认配置"""
        self.logger.warning("使用默认LLM配置")

        # 默认配置
        self.openai_enabled = False
        self.openai_api_key = ""
        self.openai_base_url = "https://api.openai.com/v1"

        self.claude_enabled = False
        self.claude_api_key = ""

        self.siliconflow_enabled = True
        self.siliconflow_api_key = os.getenv("SILICONFLOW_API_KEY", "")
        self.siliconflow_base_url = "https://api.siliconflow.com"

        self.local_enabled = False
        self.local_base_url = "http://localhost:11434"
        self.local_model = "llama2"

        self.default_provider = "siliconflow"
        self.default_temperature = 0.7
        self.default_max_tokens = 2000
        self.default_top_p = 0.9
        self.request_timeout = 30
        self.max_retries = 3
        self.retry_delay = 1.0

    def get_openai_config(self) -> Dict[str, Any]:
        """获取OpenAI配置"""
        return {
            "api_key": self.openai_api_key,
            "base_url": self.openai_base_url,
            "enabled": self.openai_enabled
        }

    def get_claude_config(self) -> Dict[str, Any]:
        """获取Claude配置"""
        return {
            "api_key": self.claude_api_key,
            "enabled": self.claude_enabled
        }

    def get_siliconflow_config(self) -> Dict[str, Any]:
        """获取SiliconFlow配置"""
        return {
            "api_key": self.siliconflow_api_key,
            "base_url": self.siliconflow_base_url,
            "default_model": self.siliconflow_default_model,
            "enabled": self.siliconflow_enabled
        }

    def get_local_config(self) -> Dict[str, Any]:
        """获取本地模型配置"""
        return {
            "base_url": self.local_base_url,
            "model": self.local_model,
            "enabled": self.local_enabled
        }

    def get_default_parameters(self) -> Dict[str, Any]:
        """获取模型默认参数"""
        return {
            "temperature": self.default_temperature,
            "max_tokens": self.default_max_tokens,
            "top_p": self.default_top_p
        }

    def get_timeout_config(self) -> Dict[str, Any]:
        """获取超时配置"""
        return {
            "request_timeout": self.request_timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay
        }

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            "openai": self.get_openai_config(),
            "claude": self.get_claude_config(),
            "siliconflow": self.get_siliconflow_config(),
            "local": self.get_local_config(),
            "default_provider": self.default_provider,
            "default_parameters": self.get_default_parameters(),
            "timeout_config": self.get_timeout_config()
        }

    def validate_config(self) -> bool:
        """验证配置有效性"""
        # 检查是否有可用的提供者
        available_providers = []

        if self.openai_enabled:
            available_providers.append("openai")
        if self.claude_enabled:
            available_providers.append("claude")
        if self.siliconflow_enabled:
            available_providers.append("siliconflow")
        if self.local_enabled:
            available_providers.append("local")

        if not available_providers:
            self.logger.error("没有可用的LLM提供者")
            return False

        # 检查默认提供者是否可用
        if self.default_provider not in available_providers:
            self.logger.warning(f"默认提供者{self.default_provider} 不在可用提供者列表中")
            self.default_provider = available_providers[0]

        self.logger.info(f"配置验证通过，可用提供者: {available_providers}")
        return True

    def is_provider_enabled(self, provider_name: str) -> bool:
        """检查提供者是否启用"""
        if provider_name == "openai":
            return self.openai_enabled
        elif provider_name == "claude":
            return self.claude_enabled
        elif provider_name == "siliconflow":
            return self.siliconflow_enabled
        elif provider_name == "local":
            return self.local_enabled
        return False

    def reload_config(self):
        """重新加载配置"""
        self._load_config()
        return self.validate_config()

    def update_config(self, new_config: Dict[str, Any]):
        """更新配置"""
        try:
            # 更新提供者配置
            if "providers" in new_config:
                providers = new_config["providers"]

                if "openai" in providers:
                    openai_config = providers["openai"]
                    self.openai_enabled = openai_config.get("enabled", self.openai_enabled)
                    self.openai_api_key = openai_config.get("api_key", self.openai_api_key)
                    self.openai_base_url = openai_config.get("base_url", self.openai_base_url)

                if "claude" in providers:
                    claude_config = providers["claude"]
                    self.claude_enabled = claude_config.get("enabled", self.claude_enabled)
                    self.claude_api_key = claude_config.get("api_key", self.claude_api_key)

                if "siliconflow" in providers:
                    sf_config = providers["siliconflow"]
                    self.siliconflow_enabled = sf_config.get("enabled", self.siliconflow_enabled)
                    self.siliconflow_api_key = sf_config.get("api_key", self.siliconflow_api_key)
                    self.siliconflow_base_url = sf_config.get("base_url", self.siliconflow_base_url)

                if "local" in providers:
                    local_config = providers["local"]
                    self.local_enabled = local_config.get("enabled", self.local_enabled)
                    self.local_base_url = local_config.get("base_url", self.local_base_url)
                    self.local_model = local_config.get("model", self.local_model)

            # 更新其他配置
            if "default_provider" in new_config:
                self.default_provider = new_config["default_provider"]

            if "default_parameters" in new_config:
                params = new_config["default_parameters"]
                self.default_temperature = float(params.get("temperature", self.default_temperature))
                self.default_max_tokens = int(params.get("max_tokens", self.default_max_tokens))
                self.default_top_p = float(params.get("top_p", self.default_top_p))

            if "timeout_config" in new_config:
                timeout = new_config["timeout_config"]
                self.request_timeout = int(timeout.get("request_timeout", self.request_timeout))
                self.max_retries = int(timeout.get("max_retries", self.max_retries))
                self.retry_delay = float(timeout.get("retry_delay", self.retry_delay))

            self.logger.info("LLM配置更新完成")
            return True

        except Exception as e:
            self.logger.error(f"更新LLM配置失败: {str(e)}")
            return False

# 全局LLM配置实例
llm_config = LLMConfig()