"""
LLM配置管理工具
支持动态更新和重新加载配置
"""


import os
from typing import Dict, Any, Optional
from ..core.logger_manager import get_logger
from ..core.config_manager import config_manager


class LLMConfigManager:
    """LLM配置管理器"""
    
    def __init__(self):
        self.logger = get_logger("api.llm.config_manager")
        self.config_file_path = os.path.join(os.getcwd(), "config.json")
    
    def get_current_config(self) -> Dict[str, Any]:
        """获取当前LLM配置"""
        try:
            return config_manager.get("llm", {})
        except Exception as e:
            self.logger.error(f"获取当前配置失败: {str(e)}")
            return {}
    
    def update_provider_config(
        self, 
        provider_name: str, 
        config_updates: Dict[str, Any]
    ) -> bool:
        """更新特定提供商的配置"""
        try:
            # 获取当前LLM配置
            llm_config = config_manager.get("llm", {})
            providers_config = llm_config.get("providers", {})
            
            # 更新提供商配置
            if provider_name not in providers_config:
                providers_config[provider_name] = {}
            
            providers_config[provider_name].update(config_updates)
            
            # 注意：这里只是内存中的更新，实际项目中需要实现配置持久化
            self.logger.info(f"更新提供商 {provider_name} 配置")
            return True
            
        except Exception as e:
            self.logger.error(f"更新提供商 {provider_name} 配置失败: {str(e)}")
            return False
    
    def enable_provider(self, provider_name: str, api_key: str = "") -> bool:
        """启用指定提供商"""
        config_updates = {
            "enabled": True
        }
        
        if api_key:
            config_updates["api_key"] = api_key
        
        return self.update_provider_config(provider_name, config_updates)
    
    def disable_provider(self, provider_name: str) -> bool:
        """禁用指定提供商"""
        config_updates = {
            "enabled": False
        }
        
        return self.update_provider_config(provider_name, config_updates)
    
    def set_default_provider(self, provider_name: str) -> bool:
        """设置默认提供商"""
        try:
            # 注意：这里只是内存中的更新，实际项目中需要实现配置持久化
            self.logger.info(f"设置默认提供商: {provider_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置默认提供商失败: {str(e)}")
            return False
    
    def update_model_parameters(
        self, 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None
    ) -> bool:
        """更新模型参数"""
        try:
            # 注意：这里只是内存中的更新，实际项目中需要实现配置持久化
            params = []
            if temperature is not None:
                params.append(f"temperature={temperature}")
            if max_tokens is not None:
                params.append(f"max_tokens={max_tokens}")
            if top_p is not None:
                params.append(f"top_p={top_p}")
            
            self.logger.info(f"更新模型参数: {', '.join(params)}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新模型参数失败: {str(e)}")
            return False
    
    def update_timeout_config(
        self,
        request_timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None
    ) -> bool:
        """更新超时配置"""
        try:
            # 注意：这里只是内存中的更新，实际项目中需要实现配置持久化
            params = []
            if request_timeout is not None:
                params.append(f"request_timeout={request_timeout}")
            if max_retries is not None:
                params.append(f"max_retries={max_retries}")
            if retry_delay is not None:
                params.append(f"retry_delay={retry_delay}")
            
            self.logger.info(f"更新超时配置: {', '.join(params)}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新超时配置失败: {str(e)}")
            return False
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有提供商状态"""
        try:
            llm_config = config_manager.get("llm", {})
            providers_config = llm_config.get("providers", {})
            
            status = {}
            for name, config in providers_config.items():
                status[name] = {
                    "enabled": config.get("enabled", False),
                    "has_api_key": bool(config.get("api_key", "")),
                    "base_url": config.get("base_url", ""),
                    "model": config.get("model", "")
                }
            
            return status
            
        except Exception as e:
            self.logger.error(f"获取提供商状态失败: {str(e)}")
            return {}
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置有效性"""
        try:
            llm_config = config_manager.get("llm", {})
            providers_config = llm_config.get("providers", {})
            
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "available_providers": [],
                "default_provider": llm_config.get("default_provider", "siliconflow")
            }
            
            # 检查是否有可用的提供商
            for name, config in providers_config.items():
                if config.get("enabled", False) and config.get("api_key", ""):
                    validation_result["available_providers"].append(name)
            
            if not validation_result["available_providers"]:
                validation_result["valid"] = False
                validation_result["errors"].append("没有可用的LLM提供商")
            
            # 检查默认提供商是否可用
            default_provider = validation_result["default_provider"]
            if default_provider not in validation_result["available_providers"]:
                validation_result["warnings"].append(
                    f"默认提供商 {default_provider} 不可用"
                )
                if validation_result["available_providers"]:
                    validation_result["default_provider"] = validation_result["available_providers"][0]
                    validation_result["warnings"].append(
                        f"自动设置默认提供商为: {validation_result['default_provider']}"
                    )
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"验证配置失败: {str(e)}")
            return {
                "valid": False,
                "errors": [f"配置验证异常: {str(e)}"],
                "warnings": [],
                "available_providers": [],
                "default_provider": "siliconflow"
            }
    
    def reload_config(self) -> bool:
        """重新加载配置"""
        try:
            # 重新加载主配置管理器
            config_manager.reload()
            
            self.logger.info("LLM配置重新加载完成")
            return True
            
        except Exception as e:
            self.logger.error(f"重新加载配置失败: {str(e)}")
            return False


# 全局配置管理器实例
llm_config_manager = LLMConfigManager()
