# -*- coding: utf-8 -*-
"""
美股个股数据提供者
从 Yahoo Finance 获取美股个股日K线数据
"""

from typing import Dict, Any, Optional, List
import requests
from datetime import datetime
import time

from utils.core.logger_manager import get_logger


class USStocksProvider:
    """美股个股数据提供者"""

    SOURCE_YAHOO = 'yahoo_finance'

    def __init__(self):
        self.logger = get_logger("us_stocks_provider")
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

    def get_daily_ohlcv(self, symbol: str, days: int = 365) -> Optional[Dict[str, Any]]:
        """
        获取个股日K线数据
        
        Args:
            symbol: 股票代码，如 'AAPL'
            days: 获取最近多少天，默认365天
            
        Returns:
            Dict包含单日数据: {
                'timestamp': '2026-03-27',
                'open': 220.5, 
                'high': 225.0, 
                'low': 219.0, 
                'close': 224.0, 
                'volume': 50000000
            }
            或 None（获取失败时）
        """
        try:
            # Yahoo Finance chart API
            urls = [
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}",
            ]
            
            for url in urls:
                try:
                    params = {'interval': '1d', 'range': f'{days}d'}
                    response = self.session.get(url, params=params, timeout=15)
                    
                    if response.status_code == 403:
                        self.logger.warning(f"Yahoo Finance 返回 403 for {symbol}，尝试备用端点")
                        continue
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    if 'chart' not in data or 'result' not in data['chart']:
                        self.logger.warning(f"Yahoo Finance 数据格式错误 for {symbol}")
                        continue
                    
                    result = data['chart']['result']
                    if not result:
                        self.logger.warning(f"Yahoo Finance 无结果 for {symbol}")
                        continue
                    
                    result = result[0]
                    if 'indicators' not in result or 'quote' not in result['indicators']:
                        self.logger.warning(f"Yahoo Finance 缺少 quote 数据 for {symbol}")
                        continue
                    
                    quote = result['indicators']['quote'][0]
                    timestamps = result['timestamp']
                    
                    # 转换为日期->数据字典
                    klines = []
                    for i, ts in enumerate(timestamps):
                        ts_date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                        
                        open_p = quote['open'][i] if quote['open'][i] is not None else 0
                        high_p = quote['high'][i] if quote['high'][i] is not None else 0
                        low_p = quote['low'][i] if quote['low'][i] is not None else 0
                        close_p = quote['close'][i] if quote['close'][i] is not None else 0
                        vol = quote['volume'][i] if quote['volume'][i] is not None else 0
                        
                        # 跳过无效数据
                        if close_p == 0 and vol == 0:
                            continue
                        
                        klines.append({
                            'timestamp': ts_date,
                            'open': round(open_p, 2),
                            'high': round(high_p, 2),
                            'low': round(low_p, 2),
                            'close': round(close_p, 2),
                            'volume': vol
                        })
                    
                    if klines:
                        self.logger.info(f"成功获取 {symbol} {len(klines)} 天K线数据")
                        return klines
                    
                except requests.exceptions.RequestException as e:
                    self.logger.debug(f"Yahoo Finance URL {url} 请求失败: {e}")
                    continue
                except Exception as e:
                    self.logger.debug(f"处理 {symbol} 数据时出错: {e}")
                    continue
            
            self.logger.warning(f"所有端点获取 {symbol} 数据均失败")
            return None
            
        except Exception as e:
            self.logger.error(f"获取 {symbol} 日K线数据异常: {e}")
            return None

    def get_batch_daily_ohlcv(self, symbols: List[str], days: int = 365) -> Dict[str, Any]:
        """
        批量获取多只个股日K线数据
        
        Args:
            symbols: 股票代码列表，如 ['AAPL', 'MSFT']
            days: 获取最近多少天，默认365天
            
        Returns:
            Dict: {
                'AAPL': [{'timestamp': '2026-03-27', 'open': 220.5, ...}, ...],
                'MSFT': [...],
                'failed': ['TSLA']  # 失败的股票列表
            }
        """
        results = {}
        failed = []
        
        for symbol in symbols:
            try:
                klines = self.get_daily_ohlcv(symbol, days)
                if klines:
                    results[symbol] = klines
                else:
                    failed.append(symbol)
            except Exception as e:
                self.logger.error(f"批量获取 {symbol} 数据失败: {e}")
                failed.append(symbol)
            
            # 避免请求过快
            time.sleep(0.5)
        
        results['failed'] = failed
        return results


# 单例模式
_us_stocks_provider_instance = None


def get_us_stocks_provider() -> USStocksProvider:
    """获取美股数据提供者单例"""
    global _us_stocks_provider_instance
    if _us_stocks_provider_instance is None:
        _us_stocks_provider_instance = USStocksProvider()
    return _us_stocks_provider_instance
