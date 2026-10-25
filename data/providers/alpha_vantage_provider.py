# -*- coding: utf-8 -*-
"""
Alpha Vantage数据提供者
提供美股技术指标、行业表现等数据
文档: https://www.alphavantage.co/documentation/
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests
from utils.core.logger_manager import get_logger


class AlphaVantageProvider:
    """Alpha Vantage数据提供者"""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str = ""):
        """
        初始化Alpha Vantage提供者
        
        Args:
            api_key: Alpha Vantage API密钥（免费额度: 25次/天）
        """
        self.logger = get_logger('alpha_vantage_provider')
        self.api_key = api_key
        self.max_retries = 3
        self.retry_delay = 1.0
        self.timeout = 30
        self._last_request_time = 0
        self.rate_limit_delay = 12  # 免费API每分钟5次，12秒间隔

    def _apply_rate_limit(self):
        """应用速率限制"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            self.logger.debug(f"速率限制，等待 {sleep_time:.2f} 秒...")
            time.sleep(sleep_time)

    def _retry_operation(self, operation, operation_name: str):
        """带重试的操作"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                self._apply_rate_limit()
                result = operation()
                self._last_request_time = time.time()
                return result
            except Exception as e:
                last_exception = e
                self.logger.warning(f"第 {attempt + 1} 次尝试 {operation_name} 失败: {e}")
                
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    self.logger.info(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)
                else:
                    self.logger.error(f"{operation_name} 重试 {self.max_retries} 次后失败")
        
        raise Exception(f"{operation_name} 失败: {last_exception}")

    def _make_request(self, params: Dict[str, Any]) -> Optional[Dict]:
        """
        发起HTTP请求
        
        Args:
            params: 请求参数
            
        Returns:
            响应数据或None
        """
        try:
            sess = requests.Session()
            adapter = requests.adapters.HTTPAdapter(max_retries=3)
            sess.mount('https://', adapter)
            
            response = sess.get(self.BASE_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Alpha Vantage API请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Alpha Vantage API处理失败: {e}")
            return None

    def get_technical_indicator(self, symbol: str, indicator: str = "MACDEXT") -> Optional[Dict]:
        """
        获取技术指标
        支持的指标: MACD, RSI, STOCH, ADX, BBANDS, CCI, ATR, etc.
        https://www.alphavantage.co/documentation/#technical-indicators
        
        Args:
            symbol: 股票代码，如 'IBM'
            indicator: 指标类型，如 'MACDEXT', 'RSI', 'SMA'
            
        Returns:
            技术指标数据
        """
        def _get_technical_indicator_internal():
            params = {
                "function": indicator,
                "symbol": symbol.upper(),
                "interval": "daily",
                "time_period": 60,
                "series_type": "close",
                "apikey": self.api_key or "demo"
            }
            return self._make_request(params)
        
        return self._retry_operation(_get_technical_indicator_internal, f"获取 {symbol} {indicator} 技术指标")

    def get_sector(self) -> Dict[str, Any]:
        """
        获取行业表现
        https://www.alphavantage.co/documentation/#sector
        
        Returns:
            行业表现数据，包含各行业ETF的实时表现
        """
        def _get_sector_internal():
            params = {
                "function": "SECTOR",
                "apikey": self.api_key or "demo"
            }
            return self._make_request(params)
        
        result = self._retry_operation(_get_sector_internal, "获取行业表现")
        if result:
            # Alpha Vantage返回的结构可能包含多个时间范围的表现
            return {
                "real_time_performance": result.get("Rank A: Real-Time Performance"),
                "1_day_performance": result.get("Rank B: 1 Day Performance"),
                "1_week_performance": result.get("Rank C: 1 Week Performance"),
                "1_month_performance": result.get("Rank D: 1 Month Performance"),
                "1_year_performance": result.get("Rank E: 1 Year Performance"),
                "ytd_performance": result.get("Rank F: Year-to-Date (YTD) Performance"),
            }
        return {}

    def get_macd(self, symbol: str, fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Dict]:
        """
        获取MACD指标
        
        Args:
            symbol: 股票代码
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
            
        Returns:
            MACD数据
        """
        def _get_macd_internal():
            params = {
                "function": "MACD",
                "symbol": symbol.upper(),
                "interval": "daily",
                "fastperiod": fast,
                "slowperiod": slow,
                "signalperiod": signal,
                "series_type": "close",
                "apikey": self.api_key or "demo"
            }
            return self._make_request(params)
        
        return self._retry_operation(_get_macd_internal, f"获取 {symbol} MACD")

    def get_rsi(self, symbol: str, period: int = 14) -> Optional[Dict]:
        """
        获取RSI指标
        
        Args:
            symbol: 股票代码
            period: RSI周期
            
        Returns:
            RSI数据
        """
        def _get_rsi_internal():
            params = {
                "function": "RSI",
                "symbol": symbol.upper(),
                "interval": "daily",
                "time_period": period,
                "series_type": "close",
                "apikey": self.api_key or "demo"
            }
            return self._retry_operation(_get_rsi_internal, f"获取 {symbol} RSI")

    def get_stoch(self, symbol: str) -> Optional[Dict]:
        """
        获取随机震荡指标(STOCH)
        
        Args:
            symbol: 股票代码
            
        Returns:
            STOCH数据
        """
        def _get_stoch_internal():
            params = {
                "function": "STOCH",
                "symbol": symbol.upper(),
                "interval": "daily",
                "apikey": self.api_key or "demo"
            }
            return self._make_request(params)
        
        return self._retry_operation(_get_stoch_internal, f"获取 {symbol} STOCH")

    def get_adx(self, symbol: str, period: int = 14) -> Optional[Dict]:
        """
        获取平均趋向指数(ADX)
        
        Args:
            symbol: 股票代码
            period: ADX周期
            
        Returns:
            ADX数据
        """
        def _get_adx_internal():
            params = {
                "function": "ADX",
                "symbol": symbol.upper(),
                "interval": "daily",
                "time_period": period,
                "apikey": self.api_key or "demo"
            }
            return self._make_request(params)
        
        return self._retry_operation(_get_adx_internal, f"获取 {symbol} ADX")

    def get_bbands(self, symbol: str, period: int = 20, std: float = 2.0) -> Optional[Dict]:
        """
        获取布林带指标
        
        Args:
            symbol: 股票代码
            period: 周期
            std: 标准差倍数
            
        Returns:
            布林带数据
        """
        def _get_bbands_internal():
            params = {
                "function": "BBANDS",
                "symbol": symbol.upper(),
                "interval": "daily",
                "time_period": period,
                "series_type": "close",
                "nbdevup": std,
                "nbdevdn": std,
                "apikey": self.api_key or "demo"
            }
            return self._make_request(params)
        
        return self._retry_operation(_get_bbands_internal, f"获取 {symbol} BBANDS")


# 单例模式
_alpha_vantage_provider_instance = None


def get_alpha_vantage_provider(api_key: str = None) -> AlphaVantageProvider:
    """获取Alpha Vantage提供者单例"""
    global _alpha_vantage_provider_instance
    if _alpha_vantage_provider_instance is None:
        if api_key is None:
            import os
            api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        _alpha_vantage_provider_instance = AlphaVantageProvider(api_key)
    return _alpha_vantage_provider_instance
