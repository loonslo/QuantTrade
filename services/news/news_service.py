# -*- coding: utf-8 -*-
"""
新闻数据服务
获取、存储和管理加密货币新闻数据
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import aiohttp
import requests
from dataclasses import dataclass

from utils.core.logger_manager import get_logger
from api.utils.task_utils import task_wrapper, record_task_execution

@dataclass
class NewsItem:
    """新闻项数据类"""
    title: str
    content: str
    url: str
    source: str
    published_at: datetime
    sentiment: Optional[str] = None
    impact_score: Optional[float] = None
    keywords: Optional[List[str]] = None
    category: Optional[str] = None

class NewsService:
    """新闻数据服务"""
    
    def __init__(self):
        self.logger = get_logger("news_service")
        self.news_sources = {
            'cryptopanic': {
                'url': 'https://cryptopanic.com/api/v1/posts/',
                'params': {
                    'auth_token': 'free',
                    'public': 'true',
                    'filter': 'hot',
                    'currencies': 'BTC,ETH,BNB,ADA,DOT,SOL,XRP,DOGE',
                    'kind': 'news'
                }
            },
            'coindesk': {
                'url': 'https://api.coindesk.com/v1/news/articles',
                'headers': {'User-Agent': 'Mozilla/5.0'}
            }
        }
    
    @task_wrapper
    async def fetch_and_store_news(self, hours_back: int = 24) -> bool:
        """获取并存储新闻数据"""
        try:
            start_time = datetime.now()
            
            # 获取新闻数据
            news_items = await self._fetch_news_from_sources(hours_back)
            
            if not news_items:
                self.logger.warning("未获取到任何新闻数据")
                return False
            
            # 存储到数据库
            stored_count = await self._store_news_to_database(news_items)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("fetch_and_store_news", True, execution_time)
            
            self.logger.info(f"新闻数据同步成功: 获取 {len(news_items)} 条，存储 {stored_count} 条")
            return True
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("fetch_and_store_news", False, execution_time)
            self.logger.error(f"新闻数据同步失败: {e}")
            raise
    
    async def _fetch_news_from_sources(self, hours_back: int) -> List[NewsItem]:
        """从多个新闻源获取数据"""
        all_news = []
        
        # 并行获取多个新闻源
        tasks = []
        for source_name, config in self.news_sources.items():
            tasks.append(self._fetch_from_single_source(source_name, config, hours_back))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                self.logger.warning(f"获取新闻源数据失败: {result}")
            elif isinstance(result, list):
                all_news.extend(result)
        
        # 去重和排序
        unique_news = self._deduplicate_news(all_news)
        return sorted(unique_news, key=lambda x: x.published_at, reverse=True)
    
    async def _fetch_from_single_source(self, source_name: str, config: Dict, hours_back: int) -> List[NewsItem]:
        """从单个新闻源获取数据"""
        news_items = []
        
        try:
            async with aiohttp.ClientSession() as session:
                if source_name == 'cryptopanic':
                    news_items = await self._fetch_cryptopanic_news(session, config, hours_back)
                elif source_name == 'coindesk':
                    news_items = await self._fetch_coindesk_news(session, config, hours_back)
                
        except Exception as e:
            self.logger.warning(f"从 {source_name} 获取新闻失败: {e}")
        
        return news_items
    
    async def _fetch_cryptopanic_news(self, session: aiohttp.ClientSession, config: Dict, hours_back: int) -> List[NewsItem]:
        """从CryptoPanic获取新闻"""
        news_items = []
        
        try:
            async with session.get(config['url'], params=config['params'], timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'results' in data:
                        cutoff_time = datetime.now() - timedelta(hours=hours_back)
                        
                        for item in data['results']:
                            try:
                                published_at = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                                
                                if published_at >= cutoff_time:
                                    news_item = NewsItem(
                                        title=item.get('title', ''),
                                        content=item.get('title', ''),  # CryptoPanic只提供标题
                                        url=item.get('url', ''),
                                        source='cryptopanic',
                                        published_at=published_at,
                                        category='crypto'
                                    )
                                    news_items.append(news_item)
                                    
                            except Exception as e:
                                self.logger.warning(f"解析CryptoPanic新闻项失败: {e}")
                                continue
                                
        except Exception as e:
            self.logger.warning(f"获取CryptoPanic新闻失败: {e}")
        
        return news_items
    
    async def _fetch_coindesk_news(self, session: aiohttp.ClientSession, config: Dict, hours_back: int) -> List[NewsItem]:
        """从CoinDesk获取新闻（示例实现）"""
        # 这里可以实现CoinDesk API调用
        # 由于CoinDesk API可能需要特殊处理，这里提供框架
        return []
    
    def _deduplicate_news(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """去重新闻"""
        seen_urls = set()
        unique_news = []
        
        for item in news_items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                unique_news.append(item)
        
        return unique_news
    
    async def _store_news_to_database(self, news_items: List[NewsItem]) -> int:
        """存储新闻到数据库"""
        try:
            from data.orm_services import get_news_service
            
            news_service = get_news_service()
            stored_count = 0
            
            for item in news_items:
                news_data = {
                    'title': item.title,
                    'content': item.content,
                    'url': item.url,
                    'source': item.source,
                    'published_at': item.published_at,
                    'sentiment': item.sentiment,
                    'impact_score': item.impact_score,
                    'keywords': ','.join(item.keywords) if item.keywords else None,
                    'category': item.category,
                    'created_at': datetime.now(),
                    'is_valid': True
                }
                
                if news_service.save_news_item(news_data):
                    stored_count += 1
            
            return stored_count
            
        except Exception as e:
            self.logger.error(f"存储新闻到数据库失败: {e}")
            return 0
    
    async def get_recent_news(self, hours_back: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的新闻数据"""
        try:
            from data.orm_services import get_news_service
            
            news_service = get_news_service()
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            return news_service.get_news_by_time_range(cutoff_time, datetime.now(), limit)
            
        except Exception as e:
            self.logger.error(f"获取最近新闻失败: {e}")
            return []
    
    async def get_news_by_keywords(self, keywords: List[str], hours_back: int = 24) -> List[Dict[str, Any]]:
        """根据关键词获取新闻"""
        try:
            from data.orm_services import get_news_service
            
            news_service = get_news_service()
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            return news_service.get_news_by_keywords(keywords, cutoff_time, datetime.now())
            
        except Exception as e:
            self.logger.error(f"根据关键词获取新闻失败: {e}")
            return []