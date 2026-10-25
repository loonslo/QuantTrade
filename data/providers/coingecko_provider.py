# -*- coding: utf-8 -*-
"""
CoinGecko数据提供者
从CoinGecko API获取加密货币数据
"""

import requests
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from utils.core.logger_manager import get_logger
from utils.time.format_utils import format_timestamp


class CoinGeckoProvider:
    """CoinGecko数据提供者"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = get_logger('coingecko_provider')
        self.api_key = api_key
        self.base_url = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': 'BACKEND/1.0',
            'Accept': 'application/json'
        })
        
        if self.api_key:
            self.session.headers.update({
                'x-cg-demo-api-key': self.api_key
            })
        
        self.logger.info("CoinGecko provider initialized")
    
    async def get_coin_details(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """获取币种详情"""
        try:
            url = f"{self.base_url}/coins/{coin_id}"
            params = {
                'localization': False,
                'tickers': False,
                'market_data': True,
                'community_data': False,
                'developer_data': False,
                'sparkline': False
            }
            
            # 使用异步请求
            response = await asyncio.to_thread(
                self.session.get, url, params=params, timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return self._process_coin_data(data)
            
        except Exception as e:
            self.logger.error(f"获取币种 {coin_id} 详情失败: {e}")
            return None
    
    async def get_global_market_data(self) -> Optional[Dict[str, Any]]:
        """获取全球市场数据"""
        try:
            url = f"{self.base_url}/global"
            
            # 使用异步请求
            response = await asyncio.to_thread(
                self.session.get, url, timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return self._process_global_data(data)
            
        except Exception as e:
            self.logger.error(f"获取全球市场数据失败: {e}")
            return None
    
    def _process_global_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理全球市场数据"""
        try:
            return {
                'total_market_cap': data.get('data', {}).get('total_market_cap', {}).get('usd', 0),
                'total_volume_24h': data.get('data', {}).get('total_volume', {}).get('usd', 0),
                'active_cryptocurrencies': data.get('data', {}).get('active_cryptocurrencies', 0),
                'markets': data.get('data', {}).get('markets', 0),
                'btc_dominance': data.get('data', {}).get('market_cap_percentage', {}).get('btc', 0),
                'eth_dominance': data.get('data', {}).get('market_cap_percentage', {}).get('eth', 0),
                'source': 'coingecko',
                'last_updated': format_timestamp(datetime.now())
            }
        except Exception as e:
            self.logger.error(f"处理全球市场数据失败: {e}")
            return None

    async def get_multiple_coins(self, coin_ids: List[str]) -> Dict[str, Any]:
        """获取多个币种的数据"""
        try:
            url = f"{self.base_url}/coins/markets"
            params = {
                'vs_currency': 'usd',
                'ids': ','.join(coin_ids),
                'order': 'market_cap_desc',
                'per_page': len(coin_ids),
                'page': 1,
                'sparkline': False,
                'price_change_percentage': '24h'
            }
            
            response = await asyncio.to_thread(
                self.session.get, url, params=params, timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            return self._process_market_data(data)
            
        except Exception as e:
            self.logger.error(f"获取多个币种数据失败: {e}")
            return {}
    
    def _process_coin_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个币种数据"""
        try:
            market_data = data.get('market_data', {})
            
            return {
                'coin_id': data.get('id'),
                'name': data.get('name'),
                'symbol': data.get('symbol'),
                'price': market_data.get('current_price', {}).get('usd', 0),
                'change_24h': market_data.get('price_change_percentage_24h', 0),
                'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                'volume_24h': market_data.get('total_volume', {}).get('usd', 0),
                'trend': self._determine_trend(market_data.get('price_change_percentage_24h', 0)),
                'rsi': None,  # CoinGecko不提供RSI，需要计算
                'support': None,  # 需要技术分析计算
                'resistance': None,  # 需要技术分析计算
                'volatility': self._calculate_volatility(market_data),
                'suggestion': self._generate_suggestion(market_data.get('price_change_percentage_24h', 0)),
                'source': 'coingecko',
                'last_updated': format_timestamp(datetime.now())
            }
            
        except Exception as e:
            self.logger.error(f"处理币种数据失败: {e}")
            return None
    
    def _process_market_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """处理市场数据"""
        result = {}
        
        for coin_data in data:
            coin_id = coin_data.get('id')
            if coin_id:
                result[coin_id] = {
                    'coin_id': coin_id,
                    'name': coin_data.get('name'),
                    'symbol': coin_data.get('symbol'),
                    'price': coin_data.get('current_price', 0),
                    'change_24h': coin_data.get('price_change_percentage_24h', 0),
                    'market_cap': coin_data.get('market_cap', 0),
                    'volume_24h': coin_data.get('total_volume', 0),
                    'trend': self._determine_trend(coin_data.get('price_change_percentage_24h', 0)),
                    'volatility': self._calculate_volatility_from_price(coin_data.get('current_price', 0)),
                    'suggestion': self._generate_suggestion(coin_data.get('price_change_percentage_24h', 0)),
                    'source': 'coingecko',
                    'last_updated': format_timestamp(datetime.now())
                }
        
        return result
    
    def _determine_trend(self, change_24h: float) -> str:
        """根据24小时变化确定趋势"""
        if change_24h > 5:
            return 'strong_bullish'
        elif change_24h > 1:
            return 'bullish'
        elif change_24h > -1:
            return 'neutral'
        elif change_24h > -5:
            return 'bearish'
        else:
            return 'strong_bearish'
    
    def _calculate_volatility(self, market_data: Dict[str, Any]) -> float:
        """计算波动率"""
        try:
            high_24h = market_data.get('high_24h', {}).get('usd', 0)
            low_24h = market_data.get('low_24h', {}).get('usd', 0)
            current_price = market_data.get('current_price', {}).get('usd', 0)
            
            if current_price > 0 and high_24h > 0 and low_24h > 0:
                volatility = (high_24h - low_24h) / current_price
                return min(volatility, 1.0)  # 限制在0-1之间
            else:
                return 0.1  # 默认波动率
        except:
            return 0.1
    
    def _calculate_volatility_from_price(self, price: float) -> float:
        """从价格计算简单波动率"""
        if price > 0:
            return min(price / 1000, 1.0)  # 简单的波动率估算
        return 0.1
    
    def _generate_suggestion(self, change_24h: float) -> str:
        """生成交易建议"""
        if change_24h > 10:
            return 'strong_buy'
        elif change_24h > 5:
            return 'buy'
        elif change_24h > 1:
            return 'weak_buy'
        elif change_24h > -1:
            return 'hold'
        elif change_24h > -5:
            return 'weak_sell'
        elif change_24h > -10:
            return 'sell'
        else:
            return 'strong_sell'
    
    def close(self):
        """关闭连接"""
        if hasattr(self, 'session'):
            self.session.close()
