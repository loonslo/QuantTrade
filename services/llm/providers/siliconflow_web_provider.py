# -*- coding: utf-8 -*-
"""
SiliconFlow Web增强提供商
支持联网查询和实时数据获取
"""

import aiohttp
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from ..llm_provider_base import BaseLLMProvider
from utils.core.logger_manager import get_logger


class SiliconFlowWebProvider(BaseLLMProvider):
    """SiliconFlow Web增强提供商 - 支持联网查询"""

    def __init__(self, api_key: str, base_url: str = "https://api.siliconflow.cn/v1", 
                 model_name: str = "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"):
        super().__init__({
            "api_key": api_key,
            "base_url": base_url,
            "model_name": model_name
        })
        self.logger = get_logger("llm.siliconflow.web")
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

    async def generate_response_with_web(self, prompt: str, enable_web_search: bool = True, **kwargs) -> str:
        """生成带联网查询的响应"""
        try:
            # 如果启用网络搜索，先获取相关信息
            web_context = ""
            if enable_web_search:
                web_context = await self._get_web_context(prompt)
            
            # 构建增强的提示词
            enhanced_prompt = self._build_enhanced_prompt(prompt, web_context)
            
            # 调用SiliconFlow API
            response = await self._call_siliconflow_api(enhanced_prompt, **kwargs)
            return response
            
        except Exception as e:
            self.logger.error(f"SiliconFlow Web生成响应失败: {str(e)}")
            raise

    async def _get_web_context(self, prompt: str) -> str:
        """获取网络上下文信息"""
        try:
            # 1. 获取加密货币市场数据
            market_data = await self._get_crypto_market_data()
            
            # 2. 获取政策新闻
            policy_news = await self._get_crypto_policy_news()
            
            # 3. 获取技术分析数据
            technical_data = await self._get_technical_analysis()
            
            # 组合所有信息
            context_parts = []
            if market_data:
                context_parts.append(f"📊 市场数据: {market_data}")
            if policy_news:
                context_parts.append(f"📰 政策新闻: {policy_news}")
            if technical_data:
                context_parts.append(f"📈 技术分析: {technical_data}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            self.logger.warning(f"获取网络上下文失败: {e}")
            return ""

    async def _get_crypto_market_data(self) -> str:
        """获取加密货币市场数据"""
        try:
            # 使用CoinGecko API获取市场数据
            async with aiohttp.ClientSession() as session:
                # 获取主要币种价格
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {
                    "ids": "bitcoin,ethereum,binancecoin",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true"
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        market_info = []
                        for coin_id, info in data.items():
                            coin_name = {"bitcoin": "BTC", "ethereum": "ETH", "binancecoin": "BNB"}.get(coin_id, coin_id.upper())
                            price = info.get("usd", 0)
                            change_24h = info.get("usd_24h_change", 0)
                            market_info.append(f"{coin_name}: ${price:,.2f} ({change_24h:+.2f}%)")
                        
                        return " | ".join(market_info)
                        
        except Exception as e:
            self.logger.warning(f"获取市场数据失败: {e}")
            return ""

    async def _get_crypto_policy_news(self) -> str:
        """获取加密货币政策新闻"""
        try:
            # 这里可以集成新闻API，比如NewsAPI、CryptoPanic等
            # 为了演示，我们返回一些模拟的政策信息
            current_time = datetime.now()
            return f"最新政策动态 (截至{current_time.strftime('%Y-%m-%d %H:%M')}): 监管环境持续完善，机构采用率提升"
            
        except Exception as e:
            self.logger.warning(f"获取政策新闻失败: {e}")
            return ""

    async def _get_technical_analysis(self) -> str:
        """获取技术分析数据"""
        try:
            # 获取恐惧贪婪指数
            async with aiohttp.ClientSession() as session:
                url = "https://api.alternative.me/fng/"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "data" in data and len(data["data"]) > 0:
                            fng_value = data["data"][0]["value"]
                            fng_classification = data["data"][0]["value_classification"]
                            return f"恐惧贪婪指数: {fng_value} ({fng_classification})"
                            
        except Exception as e:
            self.logger.warning(f"获取技术分析失败: {e}")
            return ""

    def _build_enhanced_prompt(self, original_prompt: str, web_context: str) -> str:
        """构建增强的提示词"""
        if not web_context:
            return original_prompt
        
        enhanced_prompt = f"""
基于以下实时数据进行分析：

{web_context}

用户问题: {original_prompt}

请结合上述实时数据，提供详细的分析和见解。
"""
        return enhanced_prompt.strip()

    async def _call_siliconflow_api(self, prompt: str, **kwargs) -> str:
        """调用SiliconFlow API"""
        try:
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
            self.logger.error(f"SiliconFlow API调用失败: {str(e)}")
            raise

    # 继承基类的其他方法
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """生成响应（兼容性方法）"""
        return await self.generate_response_with_web(prompt, enable_web_search=False, **kwargs)

    async def generate_stream_response(self, prompt: str, **kwargs):
        """生成流式响应（暂未实现）"""
        yield f"流式响应暂未实现: {prompt}"

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            test_prompt = "Hello"
            await self._call_siliconflow_api(test_prompt, max_tokens=10)
            return True
        except Exception as e:
            self.logger.error(f"SiliconFlow健康检查失败: {str(e)}")
            return False

    def get_provider_info(self) -> Dict[str, Any]:
        """获取提供者信息"""
        return {
            "name": "SiliconFlow Web",
            "model": self.model_name,
            "base_url": self.base_url,
            "api_key_configured": bool(self.api_key),
            "web_search_enabled": True
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
            "provider": "SiliconFlow Web",
            "model": self.model_name,
            "base_url": self.base_url,
            "available": self.is_service_available(),
            "web_search": True
        }

    def get_last_error(self) -> Optional[str]:
        """获取最后的错误信息"""
        return getattr(self, '_last_error', None)
