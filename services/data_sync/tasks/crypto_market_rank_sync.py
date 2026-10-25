# -*- coding: utf-8 -*-
"""
加密货币市场排行同步任务
从外部数据源同步市场排行数据到数据库
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import desc, and_, asc
import asyncio

from utils.time.timestamp_utils import TimestampConverter
from data.models.market_data import CryptoMarketRankings
from data.types import SymbolData
from utils.core.singleton import get_binance_provider
from ..base_service import DataSyncService

class CryptoMarketRankingsSyncTask(DataSyncService):
    """加密货币市场排行同步任务"""

    def __init__(self):
        super().__init__('crypto_market_rankings_sync')
        self.binance_provider = get_binance_provider()
        self.default_quote_assets = ['USDT', 'BTC', 'ETH']
        self.default_limit = 50

    async def _execute_sync(self):
        """执行市场排行同步"""
        self.logger.info("开始同步加密货币市场排行")
        
        try:
            total_synced = 0
            
            for quote_asset in self.default_quote_assets:
                self.logger.info(f"同步 {quote_asset} 市场排行数据...")
                
                # 从Binance获取24小时价格变动数据（同步方法放入线程池执行）
                ticker_data = await asyncio.to_thread(self.binance_provider.get_24hr_ticker_statistics)
                
                if not ticker_data:
                    self.logger.warning(f"未获取到 {quote_asset} 的ticker数据")
                    continue
                
                # 过滤指定计价货币的交易对
                filtered_data = [
                    ticker for ticker in ticker_data 
                    if ticker['symbol'].endswith(quote_asset)
                ]
                
                # 按成交量排序，取前N名
                sorted_data = sorted(
                    filtered_data, 
                    key=lambda x: float(x.get('quoteVolume', 0)), 
                    reverse=True
                )[:self.default_limit]
                
                # 转换为字典格式
                symbols_data = []
                for ticker in sorted_data:
                    try:
                        # 兼容 ccxt 风格与 REST 回退字段
                        price_val = ticker.get('last') if ticker.get('last') is not None else ticker.get('lastPrice')
                        pct_val = ticker.get('percentage') if ticker.get('percentage') is not None else ticker.get('priceChangePercent')
                        change_val = ticker.get('change') if ticker.get('change') is not None else ticker.get('priceChange')
                        # 优先使用 quoteVolume 作为成交额近似，其次使用 volume
                        vol_val = ticker.get('quoteVolume') if ticker.get('quoteVolume') is not None else ticker.get('volume')

                        symbol_data = {
                            "symbol": ticker['symbol'],
                            "quote_asset": quote_asset,
                            "price": float(price_val or 0.0),
                            "change_24h": float(pct_val or 0.0),
                            "change_amount": float(change_val or 0.0),
                            "volume_24h": float(vol_val or 0.0),
                            "market_cap": 0.0,  # Binance API不直接提供市值数据
                            "source": 'binance'
                        }
                        symbols_data.append(symbol_data)
                    except (ValueError, KeyError) as e:
                        self.logger.warning(f"解析ticker数据失败: {ticker.get('symbol', 'unknown')}, 错误: {e}")
                        continue
                
                # 保存到数据库
                if symbols_data:
                    from services.orm.crypto_market_rankings_orm import get_crypto_market_rankings_service_orm
                    service = get_crypto_market_rankings_service_orm()
                    
                    if service.save_market_rankings(symbols_data):
                        total_synced += len(symbols_data)
                        self.logger.info(f"成功同步 {len(symbols_data)} 条 {quote_asset} 市场排行数据")
                    else:
                        self.logger.error(f"保存 {quote_asset} 市场排行数据失败")
                else:
                    self.logger.warning(f"没有有效的 {quote_asset} 市场排行数据")
            
            self.logger.info(f"市场排行同步完成，总计同步 {total_synced} 条数据")
            
        except Exception as e:
            self.logger.error(f"市场排行同步失败: {e}")
            raise

    def get_task_config(self) -> Dict[str, Any]:
        """获取任务配置"""
        return {
            "task_id": "crypto_market_rankings_sync",
            "func_name": "sync_crypto_market_rankings",
            "trigger_type": "interval",
            "trigger_args": {
                "minutes": 5  # 每5分钟执行一次
            },
            "max_instances": 1,
            "coalesce": True,
            "misfire_grace_time": 60,
            "enabled": True,
            "description": "加密货币市场排行数据同步任务"
        }




# 全局任务实例
_crypto_market_rankings_sync_task: Optional[CryptoMarketRankingsSyncTask] = None

def get_crypto_market_rankings_sync_task() -> CryptoMarketRankingsSyncTask:
    """获取市场排行同步任务实例（单例模式）"""
    global _crypto_market_rankings_sync_task
    if _crypto_market_rankings_sync_task is None:
        _crypto_market_rankings_sync_task = CryptoMarketRankingsSyncTask()
    return _crypto_market_rankings_sync_task

