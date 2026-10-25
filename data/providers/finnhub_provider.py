# -*- coding: utf-8 -*-
"""
Finnhub数据提供者
提供美股基本面、实时报价、财报日历等数据
文档: https://finnhub.io/docs/api
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests
from utils.core.logger_manager import get_logger


class FinnhubProvider:
    """Finnhub数据提供者"""

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self, api_key: str = ""):
        """
        初始化Finnhub提供者
        
        Args:
            api_key: Finnhub API密钥（部分API无需key，建议配置以获取完整功能）
        """
        self.logger = get_logger('finnhub_provider')
        self.api_key = api_key
        self.max_retries = 3
        self.retry_delay = 1.0
        self.timeout = 30

    def _retry_operation(self, operation, operation_name: str):
        """带重试的操作"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                result = operation()
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

    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Optional[Dict]:
        """
        发起HTTP请求
        
        Args:
            endpoint: API端点
            params: 请求参数
            
        Returns:
            响应数据或None
        """
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            
            # 添加API密钥参数
            request_params = params.copy() if params else {}
            if self.api_key:
                request_params['token'] = self.api_key
            
            sess = requests.Session()
            adapter = requests.adapters.HTTPAdapter(max_retries=3)
            sess.mount('https://', adapter)
            
            response = sess.get(url, params=request_params, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Finnhub API请求失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Finnhub API处理失败: {e}")
            return None

    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        获取实时报价 - 不需要API key
        https://finnhub.io/api/v1/quote?symbol=AAPL
        
        Args:
            symbol: 股票代码，如 'AAPL'
            
        Returns:
            报价数据字典，包含 c(当前价格), d(涨跌额), dp(涨跌幅), h(最高), l(最低), o(开盘), pc(昨收), t(时间戳)
        """
        def _get_quote_internal():
            return self._make_request("quote", {"symbol": symbol.upper()})
        
        return self._retry_operation(_get_quote_internal, f"获取 {symbol} 报价")

    def get_basic_financials(self, symbol: str) -> Optional[Dict]:
        """
        获取基本面指标 - 需要API key
        https://finnhub.io/api/v1/stock/metric?symbol=AAPL&metric=all
        
        Args:
            symbol: 股票代码
            
        Returns:
            基本面指标数据
        """
        if not self.api_key:
            self.logger.warning(f"获取 {symbol} 基本面数据需要API key")
            return None
            
        def _get_basic_financials_internal():
            return self._make_request("stock/metric", {"symbol": symbol.upper(), "metric": "all"})
        
        return self._retry_operation(_get_basic_financials_internal, f"获取 {symbol} 基本面数据")

    def get_earnings_calendar(self, symbol: str = "", from_date: str = "", to_date: str = "") -> List[Dict]:
        """
        获取财报日历
        https://finnhub.io/api/v1/calendar/earnings?from=2026-03-01&to=2026-03-31
        
        Args:
            symbol: 股票代码（可选，空表示所有股票）
            from_date: 开始日期，格式 YYYY-MM-DD
            to_date: 结束日期，格式 YYYY-MM-DD
            
        Returns:
            财报日历列表
        """
        def _get_earnings_calendar_internal():
            params = {}
            if symbol:
                params['symbol'] = symbol.upper()
            if from_date:
                params['from'] = from_date
            if to_date:
                params['to'] = to_date
                
            return self._make_request("calendar/earnings", params)
        
        result = self._retry_operation(_get_earnings_calendar_internal, "获取财报日历")
        if result and 'earningsCalendar' in result:
            return result['earningsCalendar']
        return []

    def get_company_profile(self, symbol: str) -> Optional[Dict]:
        """
        获取公司基本信息
        https://finnhub.io/api/v1/stock/profile2?symbol=AAPL
        
        Args:
            symbol: 股票代码
            
        Returns:
            公司信息字典
        """
        def _get_company_profile_internal():
            return self._make_request("stock/profile2", {"symbol": symbol.upper()})
        
        return self._retry_operation(_get_company_profile_internal, f"获取 {symbol} 公司信息")

    def get_pe_ratio(self, symbol: str) -> Optional[float]:
        """获取市盈率"""
        data = self.get_basic_financials(symbol)
        if data and 'metric' in data:
            return data['metric'].get('peExclExtraTTM')
        return None

    def get_market_cap(self, symbol: str) -> Optional[float]:
        """获取市值"""
        data = self.get_basic_financials(symbol)
        if data and 'metric' in data:
            return data['metric'].get('marketCapitalization')
        return None

    def get_dividend_yield(self, symbol: str) -> Optional[float]:
        """获取股息率"""
        data = self.get_basic_financials(symbol)
        if data and 'metric' in data:
            return data['metric'].get('dividendYieldIndicatedAnnual')
        return None

    def get_roe(self, symbol: str) -> Optional[float]:
        """获取净资产收益率(ROE)"""
        data = self.get_basic_financials(symbol)
        if data and 'metric' in data:
            return data['metric'].get('roe')
        return None

    def get_beta(self, symbol: str) -> Optional[float]:
        """获取Beta系数"""
        data = self.get_basic_financials(symbol)
        if data and 'metric' in data:
            return data['metric'].get('beta')
        return None

    def get_revenue_growth(self, symbol: str) -> Optional[float]:
        """获取营收增长率"""
        data = self.get_basic_financials(symbol)
        if data and 'metric' in data:
            return data['metric'].get('revenueGrowth')
        return None

    def get_earnings_growth(self, symbol: str) -> Optional[float]:
        """获取盈利增长率"""
        data = self.get_basic_financials(symbol)
        if data and 'metric' in data:
            return data['metric'].get('earningsGrowth')
        return None


# 单例模式
_finnhub_provider_instance = None


def get_finnhub_provider(api_key: str = None) -> FinnhubProvider:
    """获取Finnhub提供者单例"""
    global _finnhub_provider_instance
    if _finnhub_provider_instance is None:
        if api_key is None:
            import os
            api_key = os.getenv("FINNHUB_API_KEY", "")
        _finnhub_provider_instance = FinnhubProvider(api_key)
    return _finnhub_provider_instance
