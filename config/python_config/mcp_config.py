"""
MCP服务配置文件
管理 SiliconFlow MCP 服务的配置参数
"""

import os
from typing import Dict, Any


class MCPConfig:
    """SiliconFlow MCP服务配置类"""
    
    def __init__(self):
        # SiliconFlow API 配置
        self.mcp_service_url = os.getenv("MCP_SERVICE_URL", "https://api.siliconflow.cn/v1")
        self.mcp_api_key = os.getenv("MCP_API_KEY", "")
        self.mcp_timeout = int(os.getenv("MCP_TIMEOUT", "60"))
        
        # 模型配置
        self.default_model = os.getenv("MCP_DEFAULT_MODEL", "Qwen/QwQ-32B")
        self.max_tokens = int(os.getenv("MCP_MAX_TOKENS", "4000"))
        self.temperature = float(os.getenv("MCP_TEMPERATURE", "0.7"))
        self.top_p = float(os.getenv("MCP_TOP_P", "0.9"))
        
        # 重试配置
        self.max_retries = int(os.getenv("MCP_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("MCP_RETRY_DELAY", "1"))
        
        # 缓存配置
        self.cache_enabled = os.getenv("MCP_CACHE_ENABLED", "true").lower() == "true"
        self.cache_ttl = int(os.getenv("MCP_CACHE_TTL", "300"))  # 5分钟
        
        # 健康检查配置
        self.health_check_enabled = os.getenv("MCP_HEALTH_CHECK_ENABLED", "true").lower() == "true"
        self.health_check_interval = int(os.getenv("MCP_HEALTH_CHECK_INTERVAL", "60"))  # 1分钟
        
        # 日志配置
        self.log_level = os.getenv("MCP_LOG_LEVEL", "INFO")
        self.log_requests = os.getenv("MCP_LOG_REQUESTS", "true").lower() == "true"
    
    def get_config_dict(self) -> Dict[str, Any]:
        """获取配置字典"""
        return {
            "mcp_service_url": self.mcp_service_url,
            "mcp_api_key": self.mcp_api_key if self.mcp_api_key else "未配置",
            "mcp_timeout": self.mcp_timeout,
            "default_model": self.default_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "health_check_enabled": self.health_check_enabled,
            "health_check_interval": self.health_check_interval,
            "log_level": self.log_level,
            "log_requests": self.log_requests
        }
    
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        if not self.mcp_service_url:
            return False
        
        if not self.mcp_api_key:
            return False
        
        if self.mcp_timeout <= 0:
            return False
        
        if self.max_retries < 0:
            return False
        
        if self.retry_delay < 0:
            return False
        
        if self.temperature < 0 or self.temperature > 2:
            return False
        
        if self.top_p < 0 or self.top_p > 1:
            return False
        
        return True
    
    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "QuantTradeSys-MCP-Client/1.0"
        }
        
        if self.mcp_api_key:
            headers["Authorization"] = f"Bearer {self.mcp_api_key}"
        
        return headers
    
    def get_chat_endpoint(self) -> str:
        """获取聊天完成API端点"""
        return f"{self.mcp_service_url}/chat/completions"
    
    def get_models_endpoint(self) -> str:
        """获取模型列表API端点"""
        return f"{self.mcp_service_url}/models"


# 创建全局配置实例
mcp_config = MCPConfig()
