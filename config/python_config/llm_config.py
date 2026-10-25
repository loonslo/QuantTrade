"""
LLM配置文件
管理大模型的API密钥和配置信息
"""

import os
from typing import Dict, Any, Optional, List
from utils.logger import get_logger


class LLMConfig:
    """LLM配置管理类"""
    
    def __init__(self):
        self.logger = get_logger("api.llm_config")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载LLM配置"""
        config = {
            "providers": {
                "openai": {
                    "enabled": False,
                    "api_key": None,
                    "base_url": "https://api.openai.com/v1",
                    "default_model": "gpt-4",
                    "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                    "max_tokens": 4000,
                    "temperature": 0.3
                },
                "claude": {
                    "enabled": False,
                    "api_key": None,
                    "base_url": "https://api.anthropic.com",
                    "default_model": "claude-3-sonnet-20240229",
                    "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
                    "max_tokens": 4000,
                    "temperature": 0.3
                },
                "local": {
                    "enabled": False,
                    "base_url": None,
                    "default_model": "llama2",
                    "models": ["llama2", "mistral", "codellama"],
                    "max_tokens": 2000,
                    "temperature": 0.3
                }
            },
            "default_provider": None,
            "fallback_providers": [],
            "rate_limits": {
                "requests_per_minute": 60,
                "tokens_per_minute": 10000
            },
            "timeout": {
                "request_timeout": 30,
                "connection_timeout": 10
            }
        }
        
        # 从环境变量加载配置
        self._load_from_env(config)
        
        # 设置默认提供商
        self._set_default_provider(config)
        
        return config
    
    def _load_from_env(self, config: Dict[str, Any]):
        """从环境变量加载配置"""
        # OpenAI配置
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "your-openai-key":
            config["providers"]["openai"]["enabled"] = True
            config["providers"]["openai"]["api_key"] = openai_key
            self.logger.info("OpenAI配置已加载")
        
        # Claude配置
        claude_key = os.getenv("ANTHROPIC_API_KEY")
        if claude_key and claude_key != "your-claude-key":
            config["providers"]["claude"]["enabled"] = True
            config["providers"]["claude"]["api_key"] = claude_key
            self.logger.info("Claude配置已加载")
        
        # 本地模型配置
        local_url = os.getenv("LOCAL_MODEL_URL")
        if local_url:
            config["providers"]["local"]["enabled"] = True
            config["providers"]["local"]["base_url"] = local_url
            self.logger.info(f"本地模型配置已加载: {local_url}")
        
        # 自定义配置
        custom_openai_url = os.getenv("OPENAI_BASE_URL")
        if custom_openai_url:
            config["providers"]["openai"]["base_url"] = custom_openai_url
        
        custom_claude_url = os.getenv("ANTHROPIC_BASE_URL")
        if custom_claude_url:
            config["providers"]["claude"]["base_url"] = custom_claude_url
    
    def _set_default_provider(self, config: Dict[str, Any]):
        """设置默认提供商"""
        enabled_providers = [
            name for name, provider in config["providers"].items() 
            if provider["enabled"]
        ]
        
        if enabled_providers:
            # 优先级：OpenAI > Claude > Local
            priority_order = ["openai", "claude", "local"]
            for provider in priority_order:
                if provider in enabled_providers:
                    config["default_provider"] = provider
                    break
            
            # 设置备用提供商
            config["fallback_providers"] = [
                p for p in enabled_providers if p != config["default_provider"]
            ]
            
            self.logger.info(f"默认LLM提供商: {config['default_provider']}")
            if config["fallback_providers"]:
                self.logger.info(f"备用提供商: {', '.join(config['fallback_providers'])}")
        else:
            self.logger.warning("没有可用的LLM提供商")
    
    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """获取指定提供商的配置"""
        provider_config = self.config["providers"].get(provider_name)
        if provider_config and provider_config["enabled"]:
            return provider_config
        return None
    
    def get_default_provider(self) -> Optional[str]:
        """获取默认提供商名称"""
        return self.config["default_provider"]
    
    def get_fallback_providers(self) -> List[str]:
        """获取备用提供商列表"""
        return self.config["fallback_providers"]
    
    def is_provider_available(self, provider_name: str) -> bool:
        """检查提供商是否可用"""
        provider_config = self.config["providers"].get(provider_name)
        return provider_config is not None and provider_config["enabled"]
    
    def get_available_providers(self) -> List[str]:
        """获取所有可用的提供商"""
        return [
            name for name, provider in self.config["providers"].items() 
            if provider["enabled"]
        ]
    
    def get_provider_models(self, provider_name: str) -> List[str]:
        """获取指定提供商的可用模型"""
        provider_config = self.get_provider_config(provider_name)
        if provider_config:
            return provider_config.get("models", [])
        return []
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """获取速率限制配置"""
        return self.config["rate_limits"]
    
    def get_timeout_config(self) -> Dict[str, Any]:
        """获取超时配置"""
        return self.config["timeout"]
    
    def update_provider_config(
        self, 
        provider_name: str, 
        config_updates: Dict[str, Any]
    ) -> bool:
        """更新提供商配置"""
        if provider_name not in self.config["providers"]:
            self.logger.error(f"未知的提供商: {provider_name}")
            return False
        
        try:
            provider_config = self.config["providers"][provider_name]
            provider_config.update(config_updates)
            
            # 重新设置默认提供商
            self._set_default_provider(self.config)
            
            self.logger.info(f"提供商 {provider_name} 配置已更新")
            return True
            
        except Exception as e:
            self.logger.error(f"更新提供商配置失败: {str(e)}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "default_provider": self.config["default_provider"],
            "available_providers": self.get_available_providers(),
            "fallback_providers": self.config["fallback_providers"],
            "provider_status": {
                name: {
                    "enabled": provider["enabled"],
                    "models": provider.get("models", []),
                    "configured": bool(provider.get("api_key") or provider.get("base_url"))
                }
                for name, provider in self.config["providers"].items()
            }
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置有效性"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 检查是否有可用的提供商
        available_providers = self.get_available_providers()
        if not available_providers:
            validation_result["valid"] = False
            validation_result["errors"].append("没有配置任何LLM提供商")
        
        # 检查各提供商配置
        for name, provider in self.config["providers"].items():
            if provider["enabled"]:
                if name in ["openai", "claude"] and not provider.get("api_key"):
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"{name} 提供商缺少API密钥")
                
                if name == "local" and not provider.get("base_url"):
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"{name} 提供商缺少服务地址")
        
        # 检查默认提供商
        if not self.config["default_provider"]:
            validation_result["warnings"].append("未设置默认LLM提供商")
        
        return validation_result


# 全局LLM配置实例
llm_config = LLMConfig()


def get_llm_config() -> LLMConfig:
    """获取LLM配置实例"""
    return llm_config
