# -*- coding: utf-8 -*-
"""
Yahoo Finance数据提供者
提供美股基本面数据（PE/PB/PS/ROE/营收/股息等）
无需API key，但国内访问可能需要代理
"""

import os
import re
import time
from typing import Dict, Any, Optional
import requests
from utils.core.logger_manager import get_logger


class YahooFinanceProvider:
    """Yahoo Finance数据提供者 - 专门用于获取美股基本面"""

    # Yahoo Finance v7 API
    BASE_URL = "https://query1.finance.yahoo.com"
    ALT_BASE_URL = "https://query2.finance.yahoo.com"

    def __init__(self, proxy: str = None):
        """
        初始化Yahoo Finance提供者

        Args:
            proxy: 代理地址，如 'http://127.0.0.1:7890'，None则自动从环境变量读取
        """
        self.logger = get_logger('yahoo_finance_provider')
        self.max_retries = 3
        self.retry_delay = 1.0
        self.timeout = 30

        # 代理配置
        if proxy is None:
            proxy = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("http_proxy") or os.getenv("https_proxy") or ""
        self.proxy = proxy if proxy else None
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建requests session"""
        sess = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        sess.mount('https://', adapter)

        # 设置代理
        proxies = {}
        if self.proxy:
            proxies['http'] = self.proxy
            proxies['https'] = self.proxy

        self.session.proxies.update(proxies)
        return sess

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
            request_params = params.copy() if params else {}

            response = self.session.get(url, params=request_params, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Yahoo Finance API请求失败 ({endpoint}): {e}")
            # 尝试备用URL
            try:
                url = f"{self.ALT_BASE_URL}/{endpoint}"
                response = self.session.get(url, params=request_params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except Exception:
                return None
        except Exception as e:
            self.logger.error(f"Yahoo Finance API处理失败: {e}")
            return None

    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        获取股票基本信息（PE/PB/PS/ROE/营收/股息等）
        使用 Yahoo Finance 的 /v10/finance/quoteSummary 接口

        Args:
            symbol: 股票代码，如 'AAPL'

        Returns:
            股票基本信息字典
        """
        def _get_stock_info_internal():
            # 使用 v10 API 获取 quoteSummary
            endpoint = f"v10/finance/quoteSummary/{symbol.upper()}"
            params = {
                "modules": "summaryDetail,defaultKeyStatistics,financialData,assetProfile,earnings"
            }
            data = self._make_request(endpoint, params)

            if not data:
                return None

            result = data.get("quoteSummary", {}).get("result", [])
            if not result:
                return None

            info = result[0]

            # 提取各模块数据
            summary = info.get("summaryDetail", {})
            key_stats = info.get("defaultKeyStatistics", {})
            financial = info.get("financialData", {})
            profile = info.get("assetProfile", {})
            earnings = info.get("earnings", {})

            return {
                # 估值指标
                "trailing_pe": summary.get("trailingPE", {}).get("raw"),
                "forward_pe": summary.get("forwardPE", {}).get("raw"),
                "peg_ratio": key_stats.get("pegRatio", {}).get("raw"),
                "price_to_book": summary.get("priceToBook", {}).get("raw"),
                "price_to_sales": summary.get("priceToSalesTrailing12Months", {}).get("raw"),

                # 盈利能力
                "roe": key_stats.get("returnOnEquity", {}).get("raw"),
                "roa": key_stats.get("returnOnAssets", {}).get("raw"),
                "profit_margin": financial.get("profitMargin", {}).get("raw"),
                "operating_margin": financial.get("operatingMargins", {}).get("raw"),
                "gross_margin": financial.get("grossMargins", {}).get("raw"),
                "ebitda_margin": financial.get("ebitdaMargins", {}).get("raw"),

                # 成长性
                "revenue_growth": financial.get("revenueGrowth", {}).get("raw"),
                "earnings_growth": financial.get("earningsGrowth", {}).get("raw"),
                "revenue_per_share_growth": financial.get("revenuePerShareGrowth", {}).get("raw"),
                "annual_revenue_growth": key_stats.get("annualRevenueGrowth", {}).get("raw"),
                "earnings_quarterly_growth": key_stats.get("earningsQuarterlyGrowth", {}).get("raw"),

                # 股息
                "dividend_yield": summary.get("dividendYield", {}).get("raw"),
                "dividend_rate": summary.get("dividendRate", {}).get("raw"),
                "trailing_annual_dividend_rate": summary.get("trailingAnnualDividendRate", {}).get("raw"),
                "trailing_annual_dividend_yield": summary.get("trailingAnnualDividendYield", {}).get("raw"),

                # 市值
                "market_cap": summary.get("marketCap", {}).get("raw"),
                "enterprise_value": summary.get("enterpriseValue", {}).get("raw"),
                "book_value": summary.get("bookValue", {}).get("raw"),

                # Beta
                "beta": summary.get("beta", {}).get("raw"),

                # 营收
                "total_revenue": financial.get("totalRevenue", {}).get("raw"),
                "revenue_per_share": financial.get("revenuePerShare", {}).get("raw"),
                "ebitda": financial.get("ebitda", {}).get("raw"),
                "net_income": financial.get("netIncomeToCommon", {}).get("raw"),

                # EPS
                "trailing_eps": key_stats.get("trailingEps", {}).get("raw"),
                "forward_eps": key_stats.get("forwardEps", {}).get("raw"),

                # 流通股
                "shares_outstanding": key_stats.get("sharesOutstanding", {}).get("raw"),
                "float_shares": key_stats.get("floatShares", {}).get("raw"),
                "implied_shares_outstanding": key_stats.get("impliedSharesOutstanding", {}).get("raw"),

                # 其他
                "fifty_two_week_high": summary.get("fiftyTwoWeekHigh", {}).get("raw"),
                "fifty_two_week_low": summary.get("fiftyTwoWeekLow", {}).get("raw"),
                "fifty_day_average": summary.get("fiftyDayAverage", {}).get("raw"),
                "two_hundred_day_average": summary.get("twoHundredDayAverage", {}).get("raw"),
                "analyst_target_price": financial.get("targetMeanPrice", {}).get("raw"),
                "recommendation": financial.get("recommendationKey", {}).get("raw"),
                "number_of_analyst": key_stats.get("numberOfAnalystOpinions", {}).get("raw"),

                # 公司信息
                "company_name": profile.get("companyName", ""),
                "sector": profile.get("sector", ""),
                "industry": profile.get("industry", ""),
                "country": profile.get("country", ""),
                "website": profile.get("website", ""),

                # 财报数据
                "earnings_history": earnings.get("earningsHistory", {}).get("history", []),
            }

        return self._retry_operation(_get_stock_info_internal, f"获取 {symbol} 股票信息")

    def get_key_stats(self, symbol: str) -> Optional[Dict]:
        """
        获取关键统计数据
        包含：Beta, PE, EPS, 营收, 股息等

        Args:
            symbol: 股票代码

        Returns:
            关键统计数据字典
        """
        def _get_key_stats_internal():
            info = self.get_stock_info(symbol)
            if not info:
                return None

            return {
                "symbol": symbol.upper(),
                "beta": info.get("beta"),
                "trailing_pe": info.get("trailing_pe"),
                "forward_pe": info.get("forward_pe"),
                "peg_ratio": info.get("peg_ratio"),
                "price_to_book": info.get("price_to_book"),
                "price_to_sales": info.get("price_to_sales"),
                "trailing_eps": info.get("trailing_eps"),
                "forward_eps": info.get("forward_eps"),
                "market_cap": info.get("market_cap"),
                "dividend_yield": info.get("dividend_yield"),
                "dividend_rate": info.get("dividend_rate"),
                "revenue_growth": info.get("revenue_growth"),
                "earnings_growth": info.get("earnings_growth"),
                "roe": info.get("roe"),
                "roa": info.get("roa"),
                "profit_margin": info.get("profit_margin"),
                "total_revenue": info.get("total_revenue"),
                "ebitda": info.get("ebitda"),
                "analyst_target_price": info.get("analyst_target_price"),
                "recommendation": info.get("recommendation"),
            }

        return self._retry_operation(_get_key_stats_internal, f"获取 {symbol} 关键统计")

    def get_quote(self, symbol: str) -> Optional[Dict]:
        """
        获取实时报价

        Args:
            symbol: 股票代码

        Returns:
            报价数据
        """
        def _get_quote_internal():
            endpoint = f"v7/finance/quote"
            params = {"symbols": symbol.upper()}
            data = self._make_request(endpoint, params)

            if not data:
                return None

            result = data.get("quoteResponse", {}).get("result", [])
            if not result:
                return None

            q = result[0]
            return {
                "symbol": q.get("symbol"),
                "price": q.get("regularMarketPrice"),
                "change": q.get("regularMarketChange"),
                "change_pct": q.get("regularMarketChangePercent"),
                "open": q.get("regularMarketOpen"),
                "high": q.get("regularMarketDayHigh"),
                "low": q.get("regularMarketDayLow"),
                "previous_close": q.get("regularMarketPreviousClose"),
                "volume": q.get("regularMarketVolume"),
                "market_cap": q.get("marketCap"),
                "pe_ratio": q.get("trailingPE"),
                "eps": q.get("epsTrailing"),
                "beta": q.get("beta"),
            }

        return self._retry_operation(_get_quote_internal, f"获取 {symbol} 报价")


# 单例模式
_yahoo_finance_provider_instance = None


def get_yahoo_finance_provider(proxy: str = None) -> YahooFinanceProvider:
    """获取Yahoo Finance提供者单例"""
    global _yahoo_finance_provider_instance
    if _yahoo_finance_provider_instance is None:
        _yahoo_finance_provider_instance = YahooFinanceProvider(proxy)
    return _yahoo_finance_provider_instance
