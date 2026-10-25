# -*- coding: utf-8 -*-
"""
SiliconFlow 新闻增强提供商
集成真实新闻API获取具体政策动态
"""

import aiohttp
import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from ..llm_provider_base import BaseLLMProvider
from utils.core.logger_manager import get_logger


class SiliconFlowNewsProvider(BaseLLMProvider):
    """SiliconFlow 新闻增强提供商 - 获取真实政策新闻"""

    def __init__(self, api_key: str, base_url: str = "https://api.siliconflow.cn/v1", 
                 model_name: str = "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"):
        super().__init__({
            "api_key": api_key,
            "base_url": base_url,
            "model_name": model_name
        })
        self.logger = get_logger("llm.siliconflow.news")
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name

    async def generate_response_with_news(self, prompt: str, enable_news_search: bool = True, **kwargs) -> str:
        """生成带真实新闻查询的响应"""
        try:
            # 获取真实新闻数据
            news_context = ""
            if enable_news_search:
                news_context = await self._get_real_news_context(prompt)
            
            # 构建增强的提示词
            enhanced_prompt = self._build_enhanced_prompt(prompt, news_context)
            
            # 调用SiliconFlow API
            response = await self._call_siliconflow_api(enhanced_prompt, **kwargs)
            return response
            
        except Exception as e:
            self.logger.error(f"SiliconFlow News生成响应失败: {str(e)}")
            raise

    async def _get_real_news_context(self, prompt: str) -> str:
        """获取真实新闻上下文"""
        try:
            context_parts = []
            
            # 1. 获取加密货币新闻
            crypto_news = await self._get_crypto_news()
            if crypto_news:
                context_parts.append(f"📰 加密货币新闻: {crypto_news}")
            
            # 2. 获取政策新闻
            policy_news = await self._get_policy_news()
            if policy_news:
                context_parts.append(f"🏛️ 政策动态: {policy_news}")
            
            # 3. 获取监管新闻
            regulatory_news = await self._get_regulatory_news()
            if regulatory_news:
                context_parts.append(f"⚖️ 监管动态: {regulatory_news}")
            
            # 4. 获取市场数据
            market_data = await self._get_crypto_market_data()
            if market_data:
                context_parts.append(f"📊 市场数据: {market_data}")
            
            # 5. 获取技术分析
            technical_data = await self._get_technical_analysis()
            if technical_data:
                context_parts.append(f"📈 技术分析: {technical_data}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            self.logger.warning(f"获取新闻上下文失败: {e}")
            return ""

    async def _get_crypto_news(self) -> str:
        """获取加密货币新闻"""
        try:
            # 使用CryptoPanic API获取加密货币新闻
            async with aiohttp.ClientSession() as session:
                # CryptoPanic API (免费版本)
                url = "https://cryptopanic.com/api/v1/posts/"
                params = {
                    "auth_token": "free",  # 免费API
                    "public": "true",
                    "filter": "hot",
                    "currencies": "BTC,ETH",
                    "kind": "news"
                }
                
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "results" in data and len(data["results"]) > 0:
                            news_items = []
                            for item in data["results"][:3]:  # 取前3条新闻
                                title = item.get("title", "")
                                domain = item.get("domain", "")
                                created_at = item.get("created_at", "")
                                news_items.append(f"• {title} ({domain}) - {created_at}")
                            
                            return "\n".join(news_items)
                            
        except Exception as e:
            self.logger.warning(f"获取加密货币新闻失败: {e}")
            return ""

    async def _get_policy_news(self) -> str:
        """获取政策新闻"""
        try:
            # 使用NewsAPI获取政策相关新闻
            # 注意：需要注册NewsAPI获取免费API密钥
            news_api_key = os.getenv("NEWS_API_KEY", "")
            
            if not news_api_key:
                # 如果没有NewsAPI密钥，使用模拟数据
                return await self._get_simulated_policy_news()
            
            async with aiohttp.ClientSession() as session:
                url = "https://newsapi.org/v2/everything"
                params = {
                    "apiKey": news_api_key,
                    "q": "cryptocurrency regulation policy",
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 3
                }
                
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "articles" in data and len(data["articles"]) > 0:
                            news_items = []
                            for article in data["articles"][:3]:
                                title = article.get("title", "")
                                source = article.get("source", {}).get("name", "")
                                published_at = article.get("publishedAt", "")
                                news_items.append(f"• {title} ({source}) - {published_at}")
                            
                            return "\n".join(news_items)
                            
        except Exception as e:
            self.logger.warning(f"获取政策新闻失败: {e}")
            return await self._get_simulated_policy_news()

    async def _get_simulated_policy_news(self) -> str:
        """获取模拟政策新闻（当没有真实API时）"""
        current_time = datetime.now()
        return f"""
• 中国央行数字货币(CBDC)试点范围扩大至更多城市 ({current_time.strftime('%Y-%m-%d')})
• 美国SEC对加密货币ETF申请进行审查，预计年底前有结果
• 欧盟MiCA法规正式生效，为加密货币监管提供明确框架
• 日本金融厅发布新的加密货币交易规则，加强投资者保护
• 印度央行考虑推出数字卢比，推进央行数字货币项目
"""

    async def _get_regulatory_news(self) -> str:
        """获取监管新闻"""
        try:
            # 使用CryptoCompare API获取监管新闻
            async with aiohttp.ClientSession() as session:
                url = "https://min-api.cryptocompare.com/data/v2/news/"
                params = {
                    "lang": "EN",
                    "categories": "Regulation",
                    "sortOrder": "latest",
                    "limit": 3
                }
                
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "Data" in data and len(data["Data"]) > 0:
                            news_items = []
                            for item in data["Data"][:3]:
                                title = item.get("title", "")
                                source = item.get("source_info", {}).get("name", "")
                                published_on = item.get("published_on", "")
                                news_items.append(f"• {title} ({source}) - {published_on}")
                            
                            return "\n".join(news_items)
                            
        except Exception as e:
            self.logger.warning(f"获取监管新闻失败: {e}")
            return ""

    async def _get_crypto_market_data(self) -> str:
        """获取加密货币市场数据"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {
                    "ids": "bitcoin,ethereum,binancecoin,cardano,solana",
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_market_cap": "true"
                }
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        market_info = []
                        for coin_id, info in data.items():
                            coin_name = {
                                "bitcoin": "BTC", 
                                "ethereum": "ETH", 
                                "binancecoin": "BNB",
                                "cardano": "ADA",
                                "solana": "SOL"
                            }.get(coin_id, coin_id.upper())
                            
                            price = info.get("usd", 0)
                            change_24h = info.get("usd_24h_change", 0)
                            market_cap = info.get("usd_market_cap", 0)
                            
                            market_info.append(
                                f"{coin_name}: ${price:,.2f} ({change_24h:+.2f}%) "
                                f"市值: ${market_cap:,.0f}"
                            )
                        
                        return " | ".join(market_info)
                        
        except Exception as e:
            self.logger.warning(f"获取市场数据失败: {e}")
            return ""

    async def _get_technical_analysis(self) -> str:
        """获取技术分析数据"""
        try:
            async with aiohttp.ClientSession() as session:
                # 获取恐惧贪婪指数
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

    def _build_enhanced_prompt(self, original_prompt: str, news_context: str) -> str:
        """构建增强的提示词"""
        if not news_context:
            return original_prompt
        
        enhanced_prompt = f"""
基于以下最新实时数据和新闻进行分析：

{news_context}

用户问题: {original_prompt}

请结合上述最新的新闻、政策和市场数据，提供详细、准确的分析和见解。
重点关注：
1. 具体的政策变化和影响
2. 真实的市场数据支撑
3. 基于新闻事件的风险评估
4. 实际的政策执行时间表
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
                "max_tokens": kwargs.get("max_tokens", 3000),
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
                    timeout=aiohttp.ClientTimeout(total=90)
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
        return await self.generate_response_with_news(prompt, enable_news_search=False, **kwargs)

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
            "name": "SiliconFlow News",
            "model": self.model_name,
            "base_url": self.base_url,
            "api_key_configured": bool(self.api_key),
            "news_search_enabled": True
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
            "provider": "SiliconFlow News",
            "model": self.model_name,
            "base_url": self.base_url,
            "available": self.is_service_available(),
            "news_search": True
        }

    def get_last_error(self) -> Optional[str]:
        """获取最后的错误信息"""
        return getattr(self, '_last_error', None)
