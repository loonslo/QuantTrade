# -*- coding: utf-8 -*-
"""
SiliconFlow API提供者
基于SiliconFlow API的LLM服务提供者实现
"""

import aiohttp
import json
from typing import Dict, Any, Optional
from ..llm_provider_base import BaseLLMProvider
from utils.core.logger_manager import get_logger


class SiliconFlowProvider(BaseLLMProvider):
    """SiliconFlow API提供者"""

    def __init__(self, api_key: str, base_url: str = "https://api.siliconflow.cn/v1", model_name: str = "Qwen/QwQ-32B"):
        super().__init__({
            "api_key": api_key,
            "base_url": base_url,
            "model_name": model_name
        })
        self.logger = get_logger("llm.siliconflow")
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

    async def generate_response(self, prompt: str, **kwargs) -> str:
        """生成响应"""
        try:
            # 构建请求数据
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2000),
                "top_p": kwargs.get("top_p", 0.9)
            }

            # 发送请求
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        self.logger.error(f"SiliconFlow API错误: {response.status} - {error_text}")
                        raise Exception(f"API请求失败: {response.status}")

        except Exception as e:
            self.logger.error(f"SiliconFlow生成响应失败: {str(e)}")
            raise

    async def generate_stream_response(self, prompt: str, **kwargs):
        """生成流式响应（暂未实现）"""
        # 流式响应实现
        yield f"流式响应暂未实现: {prompt}"

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 发送简单的测试请求
            test_prompt = "Hello"
            await self.generate_response(test_prompt, max_tokens=10)
            return True
        except Exception as e:
            self.logger.error(f"SiliconFlow健康检查失败: {str(e)}")
            return False

    def get_provider_info(self) -> Dict[str, Any]:
        """获取提供者信息"""
        return {
            "name": "SiliconFlow",
            "model": self.model_name,
            "base_url": self.base_url,
            "api_key_configured": bool(self.api_key)
        }

    def get_required_config_fields(self) -> list:
        """获取必需配置字段"""
        return ["api_key"]

    async def test_connection(self) -> bool:
        """测试连接"""
        return await self.health_check()

    def is_service_available(self) -> bool:
        """检查服务是否可用"""
        return bool(self.api_key)

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": "SiliconFlow",
            "model": self.model_name,
            "base_url": self.base_url,
            "available": self.is_service_available()
        }

    def get_last_error(self) -> Optional[str]:
        """获取最后的错误信息"""
        return getattr(self, '_last_error', None)
