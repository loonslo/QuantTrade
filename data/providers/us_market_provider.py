# -*- coding: utf-8 -*-
"""
美国市场数据提供者
获取纳斯达克、标普指数和美元人民币汇率数据

支持多数据源:
1. Yahoo Finance (主源)
2. Alpha Vantage (备份源)
3. Stooq (备用源)
"""

from typing import Dict, Any, Optional
import requests
from datetime import datetime, timedelta
import time
import json
import os

from utils.core.logger_manager import get_logger


class USMarketProvider:
    """美国市场数据提供者"""

    # 数据源配置
    SOURCE_YAHOO = 'yahoo_finance'
    SOURCE_ALPHA_VANTAGE = 'alpha_vantage'
    SOURCE_STOOQ = 'stooq'

    def __init__(self):
        self.logger = get_logger("us_market_provider")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        # 设置重试策略
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 从配置文件加载 Alpha Vantage API Key
        self.alpha_vantage_key = self._load_alpha_vantage_key()

    def _load_alpha_vantage_key(self) -> Optional[str]:
        """从配置文件加载 Alpha Vantage API Key"""
        try:
            config_path = "config/config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config.get('external_apis', {}).get('alpha_vantage', {}).get('api_key')
        except Exception as e:
            self.logger.warning(f"加载 Alpha Vantage API Key 失败: {e}")
        return None

    def _get_nasdaq_data_yahoo(self) -> Optional[Dict[str, Any]]:
        """从 Yahoo Finance 获取纳斯达克数据"""
        try:
            symbol = "^IXIC"
            # 尝试多个 Yahoo Finance 端点
            urls = [
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}",
            ]
            
            for url in urls:
                try:
                    params = {'interval': '1d', 'range': '5d'}
                    response = self.session.get(url, params=params, timeout=15)
                    if response.status_code == 403:
                        continue
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'chart' not in data or 'result' not in data['chart']:
                        continue
                    
                    result = data['chart']['result'][0]
                    meta = result['meta']
                    quote = result['indicators']['quote'][0]
                    timestamps = result['timestamp']
                    
                    latest_idx = -1
                    current_price = quote['close'][latest_idx]
                    if current_price is None:
                        continue
                        
                    previous_close = meta.get('chartPreviousClose', quote['close'][-2] if len(quote['close']) > 1 else current_price)
                    
                    change = current_price - previous_close
                    change_percent = (change / previous_close) * 100 if previous_close else 0
                    
                    return {
                        'symbol': 'NASDAQ',
                        'name': '纳斯达克综合指数',
                        'price': round(current_price, 2),
                        'change': round(change, 2),
                        'change_percent': round(change_percent, 2),
                        'open': round(quote['open'][latest_idx], 2) if quote['open'][latest_idx] else None,
                        'high': round(quote['high'][latest_idx], 2) if quote['high'][latest_idx] else None,
                        'low': round(quote['low'][latest_idx], 2) if quote['low'][latest_idx] else None,
                        'volume': quote['volume'][latest_idx] if quote['volume'][latest_idx] else 0,
                        'timestamp': datetime.fromtimestamp(timestamps[latest_idx]),
                        'source': self.SOURCE_YAHOO
                    }
                except Exception as e:
                    self.logger.debug(f"Yahoo Finance URL {url} 失败: {e}")
                    continue
            
            return None
        except Exception as e:
            self.logger.warning(f"Yahoo Finance 纳斯达克数据获取异常: {e}")
            return None

    def _get_nasdaq_data_alpha_vantage(self) -> Optional[Dict[str, Any]]:
        """从 Alpha Vantage 获取纳斯达克数据"""
        if not self.alpha_vantage_key:
            self.logger.debug("Alpha Vantage API Key 未配置")
            return None
            
        try:
            # Alpha Vantage 使用 NASDAQ:NASDAQ 作为指数代码
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'NASDAQ:IXIC',
                'apikey': self.alpha_vantage_key
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'Global Quote' not in data or not data['Global Quote']:
                self.logger.warning(f"Alpha Vantage 纳斯达克数据格式错误: {data}")
                return None
            
            quote = data['Global Quote']
            current_price = float(quote['05. price'])
            previous_close = float(quote['08. previous close'])
            change = current_price - previous_close
            change_percent = float(quote['10. change percent'].rstrip('%'))
            
            return {
                'symbol': 'NASDAQ',
                'name': '纳斯达克综合指数',
                'price': round(current_price, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'open': round(float(quote['02. open']), 2) if quote.get('02. open') else None,
                'high': round(float(quote['03. high']), 2) if quote.get('03. high') else None,
                'low': round(float(quote['04. low']), 2) if quote.get('04. low') else None,
                'volume': int(quote['06. volume']) if quote.get('06. volume') else 0,
                'timestamp': datetime.now(),
                'source': self.SOURCE_ALPHA_VANTAGE
            }
        except Exception as e:
            self.logger.warning(f"Alpha Vantage 纳斯达克数据获取失败: {e}")
            return None

    def _get_nasdaq_data_stooq(self) -> Optional[Dict[str, Any]]:
        """从 Stooq 获取纳斯达克数据"""
        try:
            # Stooq 使用 nasdaq100 作为指数代码
            url = "https://stooq.com/q/d/l/?s=^ndx&i=d"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            lines = response.text.strip().split('\n')
            if len(lines) < 2:
                return None
            
            # 最后一行是最新的数据
            headers = lines[0].split(',')
            data = lines[-1].split(',')
            
            row = dict(zip(headers, data))
            
            current_price = float(row['Close'])
            open_price = float(row['Open'])
            high = float(row['High'])
            low = float(row['Low'])
            volume = int(float(row['Volume'])) if row.get('Volume') else 0
            date_str = row['Date']
            
            # 获取前一天数据计算 change
            if len(lines) >= 3:
                prev_data = lines[-2].split(',')
                prev_row = dict(zip(headers, prev_data))
                previous_close = float(prev_row['Close'])
            else:
                previous_close = current_price
            
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close else 0
            
            return {
                'symbol': 'NASDAQ',
                'name': '纳斯达克综合指数',
                'price': round(current_price, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'volume': volume,
                'timestamp': datetime.strptime(date_str, '%Y-%m-%d'),
                'source': self.SOURCE_STOOQ
            }
        except Exception as e:
            self.logger.warning(f"Stooq 纳斯达克数据获取失败: {e}")
            return None

    def get_nasdaq_data(self) -> Optional[Dict[str, Any]]:
        """
        获取纳斯达克指数数据
        尝试多个数据源，按优先级:
        1. Yahoo Finance
        2. Alpha Vantage
        3. Stooq
        """
        # 尝试 Yahoo Finance
        data = self._get_nasdaq_data_yahoo()
        if data:
            self.logger.info(f"纳斯达克数据获取成功 (Yahoo Finance)")
            return data
        
        time.sleep(1)
        
        # 尝试 Alpha Vantage
        data = self._get_nasdaq_data_alpha_vantage()
        if data:
            self.logger.info(f"纳斯达克数据获取成功 (Alpha Vantage)")
            return data
        
        time.sleep(1)
        
        # 尝试 Stooq
        data = self._get_nasdaq_data_stooq()
        if data:
            self.logger.info(f"纳斯达克数据获取成功 (Stooq)")
            return data
        
        self.logger.error("所有数据源获取纳斯达克数据均失败")
        return None

    def _get_sp500_data_yahoo(self) -> Optional[Dict[str, Any]]:
        """从 Yahoo Finance 获取标普500数据"""
        try:
            symbol = "^GSPC"
            urls = [
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}",
            ]
            
            for url in urls:
                try:
                    params = {'interval': '1d', 'range': '5d'}
                    response = self.session.get(url, params=params, timeout=15)
                    if response.status_code == 403:
                        continue
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'chart' not in data or 'result' not in data['chart']:
                        continue
                    
                    result = data['chart']['result'][0]
                    meta = result['meta']
                    quote = result['indicators']['quote'][0]
                    timestamps = result['timestamp']
                    
                    latest_idx = -1
                    current_price = quote['close'][latest_idx]
                    if current_price is None:
                        continue
                        
                    previous_close = meta.get('chartPreviousClose', quote['close'][-2] if len(quote['close']) > 1 else current_price)
                    
                    change = current_price - previous_close
                    change_percent = (change / previous_close) * 100 if previous_close else 0
                    
                    return {
                        'symbol': 'SP500',
                        'name': '标普500指数',
                        'price': round(current_price, 2),
                        'change': round(change, 2),
                        'change_percent': round(change_percent, 2),
                        'open': round(quote['open'][latest_idx], 2) if quote['open'][latest_idx] else None,
                        'high': round(quote['high'][latest_idx], 2) if quote['high'][latest_idx] else None,
                        'low': round(quote['low'][latest_idx], 2) if quote['low'][latest_idx] else None,
                        'volume': quote['volume'][latest_idx] if quote['volume'][latest_idx] else 0,
                        'timestamp': datetime.fromtimestamp(timestamps[latest_idx]),
                        'source': self.SOURCE_YAHOO
                    }
                except Exception as e:
                    self.logger.debug(f"Yahoo Finance URL {url} 失败: {e}")
                    continue
            
            return None
        except Exception as e:
            self.logger.warning(f"Yahoo Finance 标普500数据获取异常: {e}")
            return None

    def _get_sp500_data_alpha_vantage(self) -> Optional[Dict[str, Any]]:
        """从 Alpha Vantage 获取标普500数据"""
        if not self.alpha_vantage_key:
            return None
            
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': 'INDEX:SPX',
                'apikey': self.alpha_vantage_key
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'Global Quote' not in data or not data['Global Quote']:
                return None
            
            quote = data['Global Quote']
            current_price = float(quote['05. price'])
            previous_close = float(quote['08. previous close'])
            change = current_price - previous_close
            change_percent = float(quote['10. change percent'].rstrip('%'))
            
            return {
                'symbol': 'SP500',
                'name': '标普500指数',
                'price': round(current_price, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'open': round(float(quote['02. open']), 2) if quote.get('02. open') else None,
                'high': round(float(quote['03. high']), 2) if quote.get('03. high') else None,
                'low': round(float(quote['04. low']), 2) if quote.get('04. low') else None,
                'volume': int(quote['06. volume']) if quote.get('06. volume') else 0,
                'timestamp': datetime.now(),
                'source': self.SOURCE_ALPHA_VANTAGE
            }
        except Exception as e:
            self.logger.warning(f"Alpha Vantage 标普500数据获取失败: {e}")
            return None

    def _get_sp500_data_stooq(self) -> Optional[Dict[str, Any]]:
        """从 Stooq 获取标普500数据"""
        try:
            url = "https://stooq.com/q/d/l/?s=^spx&i=d"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            lines = response.text.strip().split('\n')
            if len(lines) < 2:
                return None
            
            headers = lines[0].split(',')
            data = lines[-1].split(',')
            
            row = dict(zip(headers, data))
            
            current_price = float(row['Close'])
            open_price = float(row['Open'])
            high = float(row['High'])
            low = float(row['Low'])
            volume = int(float(row['Volume'])) if row.get('Volume') else 0
            date_str = row['Date']
            
            if len(lines) >= 3:
                prev_data = lines[-2].split(',')
                prev_row = dict(zip(headers, prev_data))
                previous_close = float(prev_row['Close'])
            else:
                previous_close = current_price
            
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close else 0
            
            return {
                'symbol': 'SP500',
                'name': '标普500指数',
                'price': round(current_price, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'volume': volume,
                'timestamp': datetime.strptime(date_str, '%Y-%m-%d'),
                'source': self.SOURCE_STOOQ
            }
        except Exception as e:
            self.logger.warning(f"Stooq 标普500数据获取失败: {e}")
            return None

    def get_sp500_data(self) -> Optional[Dict[str, Any]]:
        """
        获取标普500指数数据
        尝试多个数据源，按优先级:
        1. Yahoo Finance
        2. Alpha Vantage
        3. Stooq
        """
        # 尝试 Yahoo Finance
        data = self._get_sp500_data_yahoo()
        if data:
            self.logger.info(f"标普500数据获取成功 (Yahoo Finance)")
            return data
        
        time.sleep(1)
        
        # 尝试 Alpha Vantage
        data = self._get_sp500_data_alpha_vantage()
        if data:
            self.logger.info(f"标普500数据获取成功 (Alpha Vantage)")
            return data
        
        time.sleep(1)
        
        # 尝试 Stooq
        data = self._get_sp500_data_stooq()
        if data:
            self.logger.info(f"标普500数据获取成功 (Stooq)")
            return data
        
        self.logger.error("所有数据源获取标普500数据均失败")
        return None

    def _get_usdcny_data_yahoo(self) -> Optional[Dict[str, Any]]:
        """从 Yahoo Finance 获取美元人民币汇率"""
        try:
            symbol = "CNY=X"
            urls = [
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}",
            ]
            
            for url in urls:
                try:
                    params = {'interval': '1d', 'range': '5d'}
                    response = self.session.get(url, params=params, timeout=15)
                    if response.status_code == 403:
                        continue
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'chart' not in data or 'result' not in data['chart']:
                        continue
                    
                    result = data['chart']['result'][0]
                    meta = result['meta']
                    quote = result['indicators']['quote'][0]
                    timestamps = result['timestamp']
                    
                    latest_idx = -1
                    current_rate = quote['close'][latest_idx]
                    if current_rate is None:
                        continue
                    
                    previous_close = meta.get('chartPreviousClose', quote['close'][-2] if len(quote['close']) > 1 else current_rate)
                    
                    change = current_rate - previous_close
                    change_percent = (change / previous_close) * 100 if previous_close else 0
                    
                    return {
                        'symbol': 'USDCNY',
                        'name': '美元/人民币',
                        'rate': round(current_rate, 4),
                        'change': round(change, 4),
                        'change_percent': round(change_percent, 2),
                        'open': round(quote['open'][latest_idx], 4) if quote['open'][latest_idx] else None,
                        'high': round(quote['high'][latest_idx], 4) if quote['high'][latest_idx] else None,
                        'low': round(quote['low'][latest_idx], 4) if quote['low'][latest_idx] else None,
                        'timestamp': datetime.fromtimestamp(timestamps[latest_idx]),
                        'source': self.SOURCE_YAHOO
                    }
                except Exception as e:
                    self.logger.debug(f"Yahoo Finance URL {url} 失败: {e}")
                    continue
            
            return None
        except Exception as e:
            self.logger.warning(f"Yahoo Finance 美元人民币汇率获取异常: {e}")
            return None

    def _get_usdcny_data_alpha_vantage(self) -> Optional[Dict[str, Any]]:
        """从 Alpha Vantage 获取美元人民币汇率"""
        if not self.alpha_vantage_key:
            return None
            
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'CURRENCY_EXCHANGE_RATE',
                'from_currency': 'USD',
                'to_currency': 'CNY',
                'apikey': self.alpha_vantage_key
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'Realtime Currency Exchange Rate' not in data:
                return None
            
            rate_data = data['Realtime Currency Exchange Rate']
            current_rate = float(rate_data['5. Exchange Rate'])
            
            return {
                'symbol': 'USDCNY',
                'name': '美元/人民币',
                'rate': round(current_rate, 4),
                'change': 0,
                'change_percent': 0,
                'open': None,
                'high': None,
                'low': None,
                'timestamp': datetime.now(),
                'source': self.SOURCE_ALPHA_VANTAGE
            }
        except Exception as e:
            self.logger.warning(f"Alpha Vantage 美元人民币汇率获取失败: {e}")
            return None

    def _get_usdcny_data_stooq(self) -> Optional[Dict[str, Any]]:
        """从 Stooq 获取美元人民币汇率"""
        try:
            url = "https://stooq.com/q/d/l/?s=cnyusd&i=d"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            lines = response.text.strip().split('\n')
            if len(lines) < 2:
                return None
            
            headers = lines[0].split(',')
            data = lines[-1].split(',')
            
            row = dict(zip(headers, data))
            
            # Stooq 返回的是 CNY/USD，需要转换为 USD/CNY
            cny_per_usd = float(row['Close'])
            current_rate = 1.0 / cny_per_usd if cny_per_usd != 0 else 0
            
            return {
                'symbol': 'USDCNY',
                'name': '美元/人民币',
                'rate': round(current_rate, 4),
                'change': 0,
                'change_percent': 0,
                'open': None,
                'high': None,
                'low': None,
                'timestamp': datetime.strptime(row['Date'], '%Y-%m-%d'),
                'source': self.SOURCE_STOOQ
            }
        except Exception as e:
            self.logger.warning(f"Stooq 美元人民币汇率获取失败: {e}")
            return None

    def get_usdcny_rate(self) -> Optional[Dict[str, Any]]:
        """
        获取美元人民币汇率
        尝试多个数据源，按优先级:
        1. Yahoo Finance
        2. Alpha Vantage
        3. Stooq
        """
        # 尝试 Yahoo Finance
        data = self._get_usdcny_data_yahoo()
        if data:
            self.logger.info(f"美元/人民币汇率获取成功 (Yahoo Finance)")
            return data
        
        time.sleep(1)
        
        # 尝试 Alpha Vantage
        data = self._get_usdcny_data_alpha_vantage()
        if data:
            self.logger.info(f"美元/人民币汇率获取成功 (Alpha Vantage)")
            return data
        
        time.sleep(1)
        
        # 尝试 Stooq
        data = self._get_usdcny_data_stooq()
        if data:
            self.logger.info(f"美元/人民币汇率获取成功 (Stooq)")
            return data
        
        self.logger.error("所有数据源获取美元/人民币汇率均失败")
        return None

    def get_all_us_market_data(self) -> Dict[str, Any]:
        """
        获取所有美国市场数据（纳斯达克、标普500、美元人民币汇率）
        """
        result = {
            'nasdaq': None,
            'sp500': None,
            'usdcny': None,
            'updated_at': datetime.now()
        }
        
        # 获取纳斯达克数据
        nasdaq_data = self.get_nasdaq_data()
        if nasdaq_data:
            result['nasdaq'] = nasdaq_data
            self.logger.info(f"纳斯达克: {nasdaq_data['price']} ({nasdaq_data['change_percent']:+.2f}%)")
        else:
            self.logger.warning("纳斯达克数据获取失败")
        
        time.sleep(1)
        
        # 获取标普500数据
        sp500_data = self.get_sp500_data()
        if sp500_data:
            result['sp500'] = sp500_data
            self.logger.info(f"标普500: {sp500_data['price']} ({sp500_data['change_percent']:+.2f}%)")
        else:
            self.logger.warning("标普500数据获取失败")
        
        time.sleep(1)
        
        # 获取美元人民币汇率
        usdcny_data = self.get_usdcny_rate()
        if usdcny_data:
            result['usdcny'] = usdcny_data
            self.logger.info(f"美元/人民币: {usdcny_data['rate']} ({usdcny_data.get('change_percent', 0):+.2f}%)")
        else:
            self.logger.warning("美元/人民币汇率获取失败")
        
        return result


# 单例模式
_us_market_provider_instance = None

def get_us_market_provider() -> USMarketProvider:
    """获取美国市场数据提供者单例"""
    global _us_market_provider_instance
    if _us_market_provider_instance is None:
        _us_market_provider_instance = USMarketProvider()
    return _us_market_provider_instance
