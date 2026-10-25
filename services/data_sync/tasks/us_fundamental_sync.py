# -*- coding: utf-8 -*-
"""
美股基本面数据同步任务
同步11只美股的基本面数据，支持 Finnhub + Yahoo Finance fallback
"""

import asyncio
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

from utils.core.logger_manager import get_logger
from api.utils.task_utils import task_wrapper, record_task_execution
from data.providers.finnhub_provider import get_finnhub_provider
from data.providers.yahoo_finance_provider import get_yahoo_finance_provider
from data.providers.alpha_vantage_provider import get_alpha_vantage_provider
from services.orm.us_stocks_fundamental_orm import get_us_stock_fundamental_orm


class USFundamentalSyncService:
    """美股基本面数据同步服务"""

    # 美股列表
    STOCKS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'JPM', 'UNH', 'KO', 'BRK.B']

    def __init__(self, finnhub_api_key: str = "", alpha_vantage_api_key: str = "", yahoo_proxy: str = ""):
        self.logger = get_logger("us_fundamental_sync_service")
        self.finnhub_provider = get_finnhub_provider(finnhub_api_key)
        self.yahoo_provider = get_yahoo_finance_provider(yahoo_proxy or os.getenv("HTTP_PROXY"))
        self.alpha_vantage_provider = get_alpha_vantage_provider(alpha_vantage_api_key)
        self.orm = get_us_stock_fundamental_orm()

    @task_wrapper
    async def sync_all(self) -> Dict[str, bool]:
        """
        同步所有11只美股的基本面数据

        Returns:
            Dict: {'AAPL': True, 'MSFT': True, ...}
        """
        try:
            start_time = datetime.now()
            self.logger.info(f"开始同步 {len(self.STOCKS)} 只美股的基本面数据")

            results = {}
            success_list = []
            failed_list = []

            for symbol in self.STOCKS:
                try:
                    success = await asyncio.to_thread(self._sync_single_with_fallback, symbol)
                    results[symbol] = success

                    if success:
                        success_list.append(symbol)
                        self.logger.info(f"✅ {symbol} 基本面同步成功")
                    else:
                        failed_list.append(symbol)
                        self.logger.warning(f"❌ {symbol} 基本面同步失败")

                    # 避免请求过快
                    await asyncio.sleep(1)

                except Exception as e:
                    self.logger.error(f"同步 {symbol} 时异常: {e}")
                    results[symbol] = False
                    failed_list.append(symbol)

            execution_time = (datetime.now() - start_time).total_seconds()

            all_success = len(failed_list) == 0
            record_task_execution("sync_us_fundamental_all", all_success, execution_time)

            self.logger.info(f"美股基本面同步完成: 成功 {len(success_list)}, 失败 {len(failed_list)}, 耗时 {execution_time:.2f}s")
            self.logger.info(f"失败的股票: {failed_list}")

            return results

        except Exception as e:
            self.logger.error(f"同步所有美股基本面失败: {e}")
            raise

    def _sync_single_with_fallback(self, symbol: str) -> bool:
        """
        同步单只股票的基本面数据，使用 Finnhub + Yahoo Finance fallback

        策略：
        1. Finnhub 获取：PE/Beta/市值（ Finnhub 免费层有值）
        2. Yahoo Finance 获取：PB/PS/ROE/ROA/营收增长/盈利增长/股息率（Finnhub 免费层常为 None）
        3. 合并数据，Finnhub 优先，Yahoo 补缺

        Args:
            symbol: 股票代码

        Returns:
            bool: 是否成功
        """
        try:
            # 步骤1: Finnhub 获取（PE/Beta/市值）
            finnhub_quote = self.finnhub_provider.get_quote(symbol)
            finnhub_financials = self.finnhub_provider.get_basic_financials(symbol)

            # 步骤2: Yahoo Finance 获取其他字段（PB/PS/ROE/营收/股息等）
            yahoo_info = self.yahoo_provider.get_stock_info(symbol)

            # 步骤3: 合并，Finnhub 优先，Yahoo 补缺
            merged = self._merge_fundamental_data(symbol, finnhub_quote, finnhub_financials, yahoo_info)

            if not merged:
                self.logger.warning(f"未获取到 {symbol} 的任何数据")
                return False

            # 步骤4: 保存到数据库
            success = self.orm.save_fundamental(symbol, merged)

            return success

        except Exception as e:
            self.logger.error(f"同步 {symbol} 基本面失败: {e}")
            return False

    def _merge_fundamental_data(self, symbol: str, finnhub_quote: Optional[Dict],
                                finnhub_financials: Optional[Dict],
                                yahoo_info: Optional[Dict]) -> Dict[str, Any]:
        """
        合并 Finnhub 和 Yahoo Finance 的基本面数据
        Finnhub 优先，Yahoo Finance 补缺

        Args:
            symbol: 股票代码
            finnhub_quote: Finnhub 实时报价
            finnhub_financials: Finnhub 基本面指标
            yahoo_info: Yahoo Finance 基本面信息

        Returns:
            合并后的基本面数据字典
        """
        data = {
            'symbol': symbol.upper(),
            'source': 'finnhub+yahoo',
            'update_time': datetime.now().isoformat()
        }

        # 1. Finnhub 数据（优先）
        if finnhub_quote:
            data['price'] = finnhub_quote.get('c')
            if finnhub_quote.get('pc'):
                change = finnhub_quote.get('c', 0) - finnhub_quote.get('pc', 0)
                data['price_change_pct'] = (change / finnhub_quote.get('pc', 1)) * 100 if finnhub_quote.get('pc') else 0

        if finnhub_financials and 'metric' in finnhub_financials:
            metric = finnhub_financials['metric']

            # 估值 - Finnhub 有值则用 Finnhub
            data['pe_ratio'] = metric.get('peExclExtraTTM') or metric.get('peInclExtraTTM')
            data['pb_ratio'] = metric.get('pb')
            data['ps_ratio'] = metric.get('ps')

            # 盈利能力 - Finnhub 有值则用 Finnhub
            data['roe'] = metric.get('roe')
            data['roa'] = metric.get('roa')
            data['profit_margin'] = metric.get('netProfitMargin')

            # 成长性
            data['revenue_growth'] = metric.get('revenueGrowth')
            data['earnings_growth'] = metric.get('earningsGrowth')

            # 股息
            data['dividend_yield'] = metric.get('dividendYieldIndicatedAnnual')

            # 市值 - Finnhub 返回百万单位
            mc = metric.get('marketCapitalization')
            if mc:
                data['market_cap'] = mc * 1_000_000
            else:
                # 尝试从 Yahoo 获取
                if yahoo_info and yahoo_info.get('market_cap'):
                    data['market_cap'] = yahoo_info.get('market_cap')

            # Beta
            data['beta'] = metric.get('beta')

        # 2. Yahoo Finance 补缺字段
        if yahoo_info:
            # 估值补缺
            if data.get('pe_ratio') is None:
                data['pe_ratio'] = yahoo_info.get('trailing_pe') or yahoo_info.get('forward_pe')
            if data.get('pb_ratio') is None:
                data['pb_ratio'] = yahoo_info.get('price_to_book')
            if data.get('ps_ratio') is None:
                data['ps_ratio'] = yahoo_info.get('price_to_sales')

            # 盈利能力补缺
            if data.get('roe') is None:
                data['roe'] = yahoo_info.get('roe')
            if data.get('roa') is None:
                data['roa'] = yahoo_info.get('roa')
            if data.get('profit_margin') is None:
                data['profit_margin'] = yahoo_info.get('profit_margin')

            # 成长性补缺
            if data.get('revenue_growth') is None:
                data['revenue_growth'] = yahoo_info.get('revenue_growth') or yahoo_info.get('annual_revenue_growth')
            if data.get('earnings_growth') is None:
                data['earnings_growth'] = yahoo_info.get('earnings_growth')

            # 股息补缺
            if data.get('dividend_yield') is None:
                dy = yahoo_info.get('dividend_yield')
                if dy is not None:
                    data['dividend_yield'] = dy * 100 if dy < 1 else dy  # Yahoo 返回小数，DB 存百分比

            # 市值补缺
            if data.get('market_cap') is None and yahoo_info.get('market_cap'):
                data['market_cap'] = yahoo_info.get('market_cap')

            # Beta 补缺
            if data.get('beta') is None and yahoo_info.get('beta'):
                data['beta'] = yahoo_info.get('beta')

            # 额外字段（Yahoo 独有）
            data['peg_ratio'] = yahoo_info.get('peg_ratio')
            data['forward_pe'] = yahoo_info.get('forward_pe')
            data['trailing_eps'] = yahoo_info.get('trailing_eps')
            data['forward_eps'] = yahoo_info.get('forward_eps')
            data['total_revenue'] = yahoo_info.get('total_revenue')
            data['ebitda'] = yahoo_info.get('ebitda')
            data['gross_margin'] = yahoo_info.get('gross_margin')
            data['operating_margin'] = yahoo_info.get('operating_margin')
            data['analyst_target_price'] = yahoo_info.get('analyst_target_price')
            data['recommendation'] = yahoo_info.get('recommendation')

            # 公司信息
            data['company_name'] = yahoo_info.get('company_name')
            data['sector'] = yahoo_info.get('sector')
            data['industry'] = yahoo_info.get('industry')

        return data

    # ========== 以下为兼容旧接口的方法 ==========

    def _sync_single(self, symbol: str) -> bool:
        """兼容旧接口，内部调用 fallback 版本"""
        return self._sync_single_with_fallback(symbol)

    def _build_fundamental_data(self, symbol: str, quote: Dict, financials: Dict) -> Dict[str, Any]:
        """兼容旧接口，内部调用 merge 方法"""
        merged = self._merge_fundamental_data(symbol, quote, financials, None)
        return merged

    @task_wrapper
    async def sync_single_stock(self, symbol: str) -> bool:
        """
        同步单只股票的基本面数据

        Args:
            symbol: 股票代码

        Returns:
            bool: 是否成功
        """
        try:
            start_time = datetime.now()
            symbol = symbol.upper()

            if symbol not in self.STOCKS:
                self.logger.warning(f"{symbol} 不在同步列表中，将尝试同步")

            self.logger.info(f"开始同步 {symbol} 基本面数据")

            # 在线程池中执行
            success = await asyncio.to_thread(self._sync_single_with_fallback, symbol)

            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution(f"sync_us_fundamental_{symbol}", success, execution_time)

            if success:
                self.logger.info(f"✅ {symbol} 基本面同步成功，耗时 {execution_time:.2f}s")
            else:
                self.logger.warning(f"❌ {symbol} 基本面同步失败")

            return success

        except Exception as e:
            self.logger.error(f"同步 {symbol} 基本面失败: {e}")
            raise

    def get_sync_status(self) -> Dict[str, Any]:
        """获取各股票的同步状态"""
        status = {}
        for symbol in self.STOCKS:
            latest = self.orm.get_latest(symbol)

            if latest:
                history = self.orm.get_history(symbol, limit=10)
                status[symbol] = {
                    "has_data": True,
                    "latest": {
                        "timestamp": latest.get('timestamp'),
                        "pe_ratio": latest.get('pe_ratio'),
                        "roe": latest.get('roe'),
                        "price": latest.get('price'),
                        "market_cap": latest.get('market_cap')
                    },
                    "history_count": len(history)
                }
            else:
                status[symbol] = {
                    "has_data": False,
                    "latest": None,
                    "history_count": 0
                }

        return status

    def get_earnings_calendar(self, from_date: str = "", to_date: str = "") -> List[Dict[str, Any]]:
        """
        获取财报日历

        Args:
            from_date: 开始日期 YYYY-MM-DD
            to_date: 结束日期 YYYY-MM-DD

        Returns:
            财报日历列表
        """
        try:
            # 如果没有指定日期，默认获取未来30天
            if not to_date:
                from datetime import timedelta
                to_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            if not from_date:
                from_date = datetime.now().strftime('%Y-%m-%d')

            earnings = self.finnhub_provider.get_earnings_calendar(
                symbol="",
                from_date=from_date,
                to_date=to_date
            )

            # 只保留列表中的股票
            filtered_earnings = [
                e for e in earnings
                if e.get('symbol') in self.STOCKS
            ]

            return filtered_earnings

        except Exception as e:
            self.logger.error(f"获取财报日历失败: {e}")
            return []


# 单例模式
_us_fundamental_sync_service_instance = None


def get_us_fundamental_sync_service(finnhub_api_key: str = "", alpha_vantage_api_key: str = "", yahoo_proxy: str = "") -> USFundamentalSyncService:
    """获取美股基本面同步服务单例"""
    global _us_fundamental_sync_service_instance
    if _us_fundamental_sync_service_instance is None:
        _us_fundamental_sync_service_instance = USFundamentalSyncService(
            finnhub_api_key, alpha_vantage_api_key, yahoo_proxy
        )
    return _us_fundamental_sync_service_instance
