# -*- coding: utf-8 -*-
"""
数据同步服务
从外部API获取数据同步到数据库
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import asyncio
import requests

from utils.core.logger_manager import get_logger
from utils.helpers.constants import ConfigConstants
from api.utils.task_utils import task_wrapper, record_task_execution
# 注意：这里需要导入provider和service函数
from utils.core.singleton import get_binance_provider
from data.orm_services import (
    get_crypto_market_rankings_service,
    get_market_overview_service,
)

class DataSyncService:
    """数据同步服务"""

    def __init__(self):
        self.logger = get_logger("data_sync_service")
        # 获取provider实例，启用期货功能以获取持仓量和资金费率数据
        self.provider = get_binance_provider(enable_futures=True)

    @task_wrapper
    async def sync_fear_greed_index(self) -> bool:
        """
        同步恐惧贪婪指数。

        目标：从外部接口获取当前恐惧贪婪指数，并保存到`MarketOverview`相关服务。
        思路：
        1. 使用统一的HTTP工具方法获取JSON数据（避免在异步函数中阻塞）。
        2. 解析最新一条指数值与分类，并补充中文分类说明。
        3. 通过ORM服务进行持久化，记录任务执行耗时。
        """
        try:
            start_time = datetime.now()
            # 统一从辅助方法获取恐惧贪婪指数数据
            fng = await self._fetch_fear_greed_index()

            if fng is None:
                raise ValueError("无法获取恐惧贪婪指数数据")

            value, classification = fng

            # 构造缓存数据
            cache_data: Dict[str, Any] = {
                "value": value,
                "classification": classification,
                "classification_cn": self._get_classification_cn(classification),
                "updated_at": datetime.now(),
                "source": "alternative.me",
                "is_valid": True,
            }

            # 使用市场概览服务保存恐惧贪婪指数
            market_overview_service = get_market_overview_service()
            if not market_overview_service.save_fear_greed_index(cache_data):
                raise Exception("保存恐惧贪婪指数到MarketOverview表失败")

            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("sync_fear_greed_index", True, execution_time)

            self.logger.info(f"恐惧贪婪指数同步成功: {value} ({classification})")
            return True

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("sync_fear_greed_index", False, execution_time)
            self.logger.error(f"恐惧贪婪指数同步失败: {e}")
            raise

    @task_wrapper
    async def sync_top_symbols(self, quote_asset: str = 'USDT') -> bool:
        """
        同步前20名币种数据。

        目标：针对一个或多个计价资产（如USDT/USDC），获取交易所前20名交易对信息并保存。
        说明：
        - provider调用在后台线程执行，避免阻塞事件循环。
        - 当某个计价资产未返回数据时，记录警告并继续处理其他资产。
        """
        try:
            start_time = datetime.now()

            # 处理多个计价资产，支持 "USDT,USDC,BUSD"
            if isinstance(quote_asset, str):
                quote_assets = [q.strip() for q in quote_asset.split(',') if q.strip()]
            else:
                quote_assets = [ConfigConstants.DEFAULT_QUOTE_ASSET]

            overall_saved = 0

            for qa in quote_assets:
                # 在线程池中调用provider获取数据
                data = await asyncio.to_thread(self.provider.get_top_20_symbols, qa)

                if data:
                    # 转换为列表格式
                    cache_data: List[Dict[str, Any]] = []
                    for symbol, info in data.items():
                        cache_data.append({
                            "symbol": symbol,
                            "quote_asset": qa,
                            "price": info.get("price", 0),
                            "change_24h": info.get("change_24h", 0),
                            "change_amount": info.get("change_amount", 0),
                            "volume_24h": info.get("volume", 0),
                            "market_cap": info.get("market_cap", 0),
                            "rank": info.get("rank", 0),
                            "source": "binance",
                            "is_valid": True,
                            "updated_at": datetime.now()
                        })

                    # 保存到数据库使用CryptoMarketRankingsService 保存数据
                    market_rankings_service = get_crypto_market_rankings_service()
                    if not market_rankings_service.save_market_rankings(cache_data):
                        raise Exception("保存前20名币种到数据库失败")
                    overall_saved += len(cache_data)
                else:
                    self.logger.warning(f"从 {qa} 获取前20名币种失败，返回数据为空")

            if overall_saved == 0:
                raise ValueError("无法获取任何计价资产的前20名币种")

            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("sync_top_symbols", True, execution_time)
            self.logger.info(f"前20名币种同步成功: {overall_saved} 个记录，来源: {quote_assets}")
            return True

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("sync_top_symbols", False, execution_time)
            self.logger.error(f"前20名币种同步失败: {e}")
            raise

        

    @task_wrapper
    async def sync_market_overview(self) -> bool:
        """
        同步市场概览。

        目标：聚合BTC/ETH详情、恐惧贪婪指数、24小时成交量、全球总市值与主导率等信息，写入数据库。
        """
        try:
            start_time = datetime.now()

            # 获取市场概览
            overview_data = await self._build_market_overview()

            # 使用市场概览服务保存数据
            market_overview_service = get_market_overview_service()
            if not market_overview_service.save_market_overview(overview_data):
                raise Exception("保存市场概览到MarketOverview表失败")

            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("sync_market_overview", True, execution_time)

            self.logger.info("市场概览同步成功")
            return True

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("sync_market_overview", False, execution_time)
            self.logger.error(f"市场概览同步失败: {e}")
            raise

    @task_wrapper
    async def sync_market_data_1m(self, symbols: Optional[List[str]] = None) -> bool:
        """同步1分钟市场K线数据（已弃用，统一走代理）"""
        self.logger.warning("sync_market_data_1m 方法已弃用，请使用代理统一调用 KlineDataSyncService")
        return await self._delegate_kline_sync("1m", symbols)

    @task_wrapper
    async def sync_market_data_1d(self, symbols: Optional[List[str]] = None) -> bool:
        """同步1天市场K线数据（已弃用，统一走代理）"""
        self.logger.warning("sync_market_data_1d 方法已弃用，请使用代理统一调用 KlineDataSyncService")
        return await self._delegate_kline_sync("1d", symbols)

    @task_wrapper
    async def sync_market_data_3m(self, symbols: Optional[List[str]] = None) -> bool:
        """同步3分钟市场K线数据（已弃用，统一走代理）"""
        self.logger.warning("sync_market_data_3m 方法已弃用，请使用代理统一调用 KlineDataSyncService")
        return await self._delegate_kline_sync("3m", symbols)

    @task_wrapper
    async def sync_market_data_5m(self, symbols: Optional[List[str]] = None) -> bool:
        """同步5分钟市场K线数据（已弃用，统一走代理）"""
        self.logger.warning("sync_market_data_5m 方法已弃用，请使用代理统一调用 KlineDataSyncService")
        return await self._delegate_kline_sync("5m", symbols)

    @task_wrapper
    async def sync_market_data_15m(self, symbols: Optional[List[str]] = None) -> bool:
        """同步15分钟市场K线数据（已弃用，统一走代理）"""
        self.logger.warning("sync_market_data_15m 方法已弃用，请使用代理统一调用 KlineDataSyncService")
        return await self._delegate_kline_sync("15m", symbols)

    @task_wrapper
    async def sync_market_data_1h(self, symbols: Optional[List[str]] = None) -> bool:
        """同步1小时市场K线数据（已弃用，统一走代理）"""
        self.logger.warning("sync_market_data_1h 方法已弃用，请使用代理统一调用 KlineDataSyncService")
        return await self._delegate_kline_sync("1h", symbols)

    @task_wrapper
    async def sync_market_data_4h(self, symbols: Optional[List[str]] = None) -> bool:
        """同步4小时市场K线数据（已弃用，统一走代理）"""
        self.logger.warning("sync_market_data_4h 方法已弃用，请使用代理统一调用 KlineDataSyncService")
        return await self._delegate_kline_sync("4h", symbols)

    @task_wrapper
    async def cleanup_old_cache(self) -> bool:
        """
        清理过期缓存数据。

        说明：预留接口，后续可接入缓存表的过期策略（如按时间戳批量清理）。
        当前实现仅记录任务执行成功的次数。
        """
        try:
            start_time = datetime.now()

            # 清理过期数据
            # 这里可以添加清理逻辑
            cleaned_count = 0

            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("cleanup_old_cache", True, execution_time)

            self.logger.info(f"过期缓存数据清理完成: {cleaned_count} 个")
            return True

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("cleanup_old_cache", False, execution_time)
            self.logger.error(f"过期缓存数据清理失败: {e}")
            raise

    @task_wrapper
    async def database_maintenance(self) -> bool:
        """
        数据库维护任务。

        说明：预留接口，可按需加入 VACUUM、ANALYZE 或统计信息刷新等操作。
        """
        try:
            start_time = datetime.now()

            # 执行数据库维护操作
            # 可以添加 VACUUM、ANALYZE 等操作

            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("database_maintenance", True, execution_time)

            self.logger.info("数据库维护完成")
            return True

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("database_maintenance", False, execution_time)
            self.logger.error(f"数据库维护失败: {e}")
            raise

    # 辅助方法
    def _get_classification_cn(self, classification: str) -> str:
        """
        获取恐惧贪婪指数的中文分类。

        参数：classification 英文分类，如 'Extreme Fear'。
        返回：对应的中文描述，如 '极度恐惧'。
        """
        cn_map = {
            'Extreme Fear': '极度恐惧',
            'Fear': '恐惧',
            'Neutral': '中性',
            'Greed': '贪婪',
            'Extreme Greed': '极度贪婪'
        }
        return cn_map.get(classification, '中性')

    async def _get_coin_details_single(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取单个币种详情（简化版）。

        说明：这里可接入技术分析模块，当前仅做占位，返回简单的价格与区间信息。
        """
        try:
            # 这里可以调用技术分析模块
            # 暂时使用简单实现
            price_data = self.provider.get_latest_price(symbol)
            if not price_data:
                return None

            return {
                "price": price_data["price"],
                "change_24h": price_data["change_24h"],
                "trend": "neutral",
                "support": price_data["price"] * 0.95,
                "resistance": price_data["price"] * 1.05,
                "suggestion": "数据同步中，建议等待",
                "rsi": 50.0,
                "macd_line": 0.0,
                "macd_signal": 0.0,
                "macd_histogram": 0.0,
                "bb_upper": price_data["price"] * 1.05,
                "bb_middle": price_data["price"],
                "bb_lower": price_data["price"] * 0.95,
                "volume_analysis": "数据同步中",
                "volatility": 0.0,
                "source": "data_sync"
            }
        except Exception as e:
            self.logger.warning(f"获取币种 {symbol} 详情失败: {e}")
            return None

    async def _build_market_overview(self) -> Dict[str, Any]:
        """
        构建市场概览。

        聚合来源：
        - CoinGecko：BTC/ETH详情、全球市值与主导率。
        - 自身provider：24小时交易量（USDT计价对汇总）。
        - alternative.me：恐惧贪婪指数（通过统一辅助方法获取）。
        """
        try:
            # 使用CoinGecko API获取所有数据
            from data.providers.coingecko_provider import CoinGeckoProvider
            coingecko = CoinGeckoProvider()
            
            # 获取BTC和ETH详情
            btc_details = None
            eth_details = None
            
            try:
                btc_details = await coingecko.get_coin_details('bitcoin')
                if btc_details:
                    self.logger.info(f"成功获取BTC详情: 价格 ${btc_details.get('price', 0):,.2f}")
                else:
                    self.logger.warning("获取BTC详情失败")
            except Exception as e:
                self.logger.warning(f"获取BTC详情失败: {e}")
                btc_details = None
            
            try:
                eth_details = await coingecko.get_coin_details('ethereum')
                if eth_details:
                    self.logger.info(f"成功获取ETH详情: 价格 ${eth_details.get('price', 0):,.2f}")
                else:
                    self.logger.warning("获取ETH详情失败")
            except Exception as e:
                self.logger.warning(f"获取ETH详情失败: {e}")
                eth_details = None

            # 获取恐惧贪婪指数（经由统一辅助方法）
            fear_greed = None
            try:
                fng = await self._fetch_fear_greed_index()
                if fng:
                    value, classification = fng
                    fear_greed = {"value": value, "classification": classification}
                    self.logger.info(f"成功获取恐惧贪婪指数: {fear_greed}")
            except Exception as e:
                self.logger.warning(f"获取恐惧贪婪指数失败: {e}")

            # 从CoinGecko数据中获取价格
            btc_price = btc_details.get("price", 0) if btc_details else 0
            eth_price = eth_details.get("price", 0) if eth_details else 0
            
            # 获取24小时交易量数据
            total_volume_24h = 0
            try:
                # 获取24小时ticker统计，包含交易量
                ticker_24h = await asyncio.to_thread(self.provider.get_24hr_ticker_statistics)
                if ticker_24h:
                    # 计算所有USDT交易对的总交易量
                    total_volume_24h = sum(float(ticker.get('quoteVolume', 0)) for ticker in ticker_24h 
                                         if ticker.get('symbol', '').endswith('USDT'))
                    self.logger.info(f"计算得出24小时总交易量: {total_volume_24h:,.2f}")
                else:
                    self.logger.warning("获取24小时ticker统计失败，交易量设为0")
            except Exception as e:
                self.logger.warning(f"获取24小时交易量失败: {e}")
                total_volume_24h = 0
            
            # 获取全球市场数据 (使用CoinGecko API获取真实数据)
            estimated_market_cap = 0
            btc_dominance = 0
            eth_dominance = 0
            
            try:
                # 获取CoinGecko全球市场数据
                global_data = await coingecko.get_global_market_data()
                if global_data:
                    estimated_market_cap = global_data.get('total_market_cap', 0)
                    btc_dominance = global_data.get('btc_dominance', 0)
                    eth_dominance = global_data.get('eth_dominance', 0)
                    
                    self.logger.info(f"从CoinGecko获取全球总市值: {estimated_market_cap:,.2f}")
                    self.logger.info(f"BTC主导率: {btc_dominance:.2f}%, ETH主导率: {eth_dominance:.2f}%")
                else:
                    self.logger.warning("CoinGecko API未返回有效的全球市场数据")
                    estimated_market_cap = 0
                    btc_dominance = 0
                    eth_dominance = 0
                    
            except Exception as e:
                self.logger.warning(f"获取全球市场数据失败: {e}")
                estimated_market_cap = 0
                btc_dominance = 0
                eth_dominance = 0

            return {
                "total_market_cap": estimated_market_cap,
                "total_volume_24h": total_volume_24h,
                "market_trend": "bullish" if btc_price > 50000 else "bearish" if btc_price < 30000 else "neutral",
                "risk_level": "high" if btc_price < 30000 else "low" if btc_price > 60000 else "medium",
                "btc_dominance": btc_dominance,
                "eth_dominance": eth_dominance,
                "fear_greed_value": fear_greed.get("value", 50) if fear_greed else 50,
                "fear_greed_classification": fear_greed.get("classification", "Neutral") if fear_greed else "Neutral",
                "source": "data_sync",
                "btc_price": btc_price,
                "eth_price": eth_price
            }
        except Exception as e:
            self.logger.error(f"构建市场概览失败: {e}")
            return {
                "total_market_cap": 0,
                "total_volume_24h": 0,
                "market_trend": "neutral",
                "risk_level": "medium",
                "btc_dominance": 0,
                "eth_dominance": 0,
                "fear_greed_value": 50,
                "fear_greed_classification": "Neutral",
                "source": "data_sync",
                "btc_price": 0,
                "eth_price": 0
            }

    # =====================
    # 内部通用辅助方法
    # =====================

    async def _request_json(self, url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        统一的HTTP JSON请求（在线程池中执行，避免阻塞事件循环）。

        返回：成功返回dict，失败返回None。
        """
        try:
            def _do_request() -> Dict[str, Any]:
                resp = requests.get(url, timeout=timeout)
                resp.raise_for_status()
                return resp.json()

            return await asyncio.to_thread(_do_request)
        except Exception as e:
            self.logger.warning(f"请求URL失败: {url}, 错误: {e}")
            return None

    async def _fetch_fear_greed_index(self) -> Optional[Tuple[int, str]]:
        """
        获取恐惧贪婪指数的值与英文分类。

        返回：(value, classification) 或 None。
        """
        url = "https://api.alternative.me/fng/"
        data = await self._request_json(url, timeout=10)
        if not data or not data.get("data"):
            return None
        try:
            latest = data["data"][0]
            value = int(latest["value"])  # 例如 56
            classification = latest["value_classification"]  # 例如 "Greed"
            return value, classification
        except Exception as e:
            self.logger.warning(f"解析恐惧贪婪指数数据失败: {e}")
            return None

    async def _delegate_kline_sync(self, interval: str, symbols: Optional[List[str]]) -> bool:
        """
        统一代理到 KlineDataSyncService 的K线同步方法，减少重复代码。

        参数：
        - interval: 时间粒度（如 '1m', '5m', '1h', '1d'）
        - symbols: 指定币对列表，为空表示默认集合
        """
        from services.data_sync.tasks.kline_data_sync import get_kline_data_sync_service
        kline_sync_service = get_kline_data_sync_service()
        return await kline_sync_service.manual_sync_kline_data(interval, symbols, 1)

    @task_wrapper
    async def sync_us_market_data(self) -> bool:
        """
        同步美国市场数据（纳斯达克、标普500、美元人民币汇率）
        代理到USMarketSyncService
        """
        from services.data_sync.tasks.us_market_sync import get_us_market_sync_service
        us_market_sync_service = get_us_market_sync_service()
        return await us_market_sync_service.sync_us_market_data()

    @task_wrapper
    async def sync_all_qdii_funds(self) -> bool:
        """
        同步QDII基金数据（纳斯达克和标普相关）
        代理到QDIIFundSyncService
        """
        from services.data_sync.tasks.qdii_fund_sync import get_qdii_fund_sync_service
        qdii_fund_sync_service = get_qdii_fund_sync_service()
        return await qdii_fund_sync_service.sync_all_qdii_funds()

__all__ = [
    'DataSyncService'
]