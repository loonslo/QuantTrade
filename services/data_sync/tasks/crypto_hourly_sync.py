# -*- coding: utf-8 -*-
"""
加密货币小时K线数据同步任务
同步主流币种的1H/4H K线数据
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List

from utils.core.logger_manager import get_logger
from api.utils.task_utils import task_wrapper, record_task_execution
from data.providers.binance_provider import BinanceDataProvider
from services.orm.crypto_hourly_kline_orm import get_crypto_hourly_kline_orm


class CryptoHourlySyncService:
    """加密货币小时K线数据同步服务"""

    # 主流币种列表
    SYMBOLS = [
        'BTC/USDT',
        'ETH/USDT',
        'BNB/USDT',
        'SOL/USDT',
        'XRP/USDT',
        'ADA/USDT',
        'DOGE/USDT',
        'AVAX/USDT',
        'DOT/USDT',
        'MATIC/USDT',
        'LINK/USDT',
        'UNI/USDT',
        'ATOM/USDT',
        'LTC/USDT',
        'BCH/USDT'
    ]

    # 支持的周期
    INTERVALS = ['1h', '4h']

    # 每次同步获取的K线条数
    DEFAULT_LIMIT = 500

    def __init__(self):
        self.logger = get_logger("crypto_hourly_sync_service")
        self.provider = BinanceDataProvider()
        self.orm = get_crypto_hourly_kline_orm()

    @task_wrapper
    async def sync_all(self, symbols: List[str] = None, intervals: List[str] = None, limit: int = None) -> Dict[str, bool]:
        """
        同步所有指定币种和周期的K线数据
        
        Args:
            symbols: 币种列表，默认使用 SYMBOLS
            intervals: 周期列表，默认使用 INTERVALS
            limit: 每次同步获取的条数
            
        Returns:
            Dict: {'BTC/USDT_1h': True, 'BTC/USDT_4h': True, ...}
        """
        try:
            start_time = datetime.now()
            
            if symbols is None:
                symbols = self.SYMBOLS
            if intervals is None:
                intervals = self.INTERVALS
            if limit is None:
                limit = self.DEFAULT_LIMIT
            
            self.logger.info(f"开始同步加密货币小时K线: {len(symbols)} 币种, {len(intervals)} 周期")

            results = {}
            success_count = 0
            fail_count = 0

            for symbol in symbols:
                for interval in intervals:
                    try:
                        key = f"{symbol}_{interval}"
                        success = await asyncio.to_thread(self._sync_single, symbol, interval, limit)
                        results[key] = success
                        
                        if success:
                            success_count += 1
                            self.logger.info(f"✅ {symbol} {interval} 同步成功")
                        else:
                            fail_count += 1
                            self.logger.warning(f"❌ {symbol} {interval} 同步失败")
                        
                        # 避免请求过快
                        await asyncio.sleep(0.3)
                        
                    except Exception as e:
                        self.logger.error(f"同步 {symbol} {interval} 时异常: {e}")
                        results[f"{symbol}_{interval}"] = False
                        fail_count += 1

            execution_time = (datetime.now() - start_time).total_seconds()
            all_success = fail_count == 0
            record_task_execution("sync_crypto_hourly_all", all_success, execution_time)
            
            self.logger.info(f"加密货币小时K线同步完成: 成功 {success_count}, 失败 {fail_count}, 耗时 {execution_time:.2f}s")
            
            return results

        except Exception as e:
            self.logger.error(f"同步所有加密货币小时K线失败: {e}")
            raise

    def _sync_single(self, symbol: str, interval: str, limit: int) -> bool:
        """
        同步单个币种的单个周期K线数据
        
        Args:
            symbol: 交易对
            interval: 时间周期
            limit: 数据条数
            
        Returns:
            bool: 是否成功
        """
        try:
            # 获取K线数据
            klines = self.provider.get_hourly_ohlcv(symbol, interval, limit)
            
            if not klines:
                self.logger.warning(f"未获取到 {symbol} {interval} 的K线数据")
                return False
            
            # 保存到数据库
            success = self.orm.save_batch_hourly_kline(symbol, klines, interval)
            
            return success

        except Exception as e:
            self.logger.error(f"同步 {symbol} {interval} 失败: {e}")
            return False

    @task_wrapper
    async def sync_single_symbol(self, symbol: str, intervals: List[str] = None, limit: int = None) -> Dict[str, bool]:
        """
        同步单个币种的K线数据
        
        Args:
            symbol: 交易对
            intervals: 周期列表
            limit: 数据条数
            
        Returns:
            Dict: {'1h': True, '4h': True}
        """
        try:
            start_time = datetime.now()
            symbol = symbol.upper()
            
            if intervals is None:
                intervals = self.INTERVALS
            if limit is None:
                limit = self.DEFAULT_LIMIT
            
            self.logger.info(f"开始同步 {symbol} 的K线数据")
            
            results = {}
            for interval in intervals:
                success = await asyncio.to_thread(self._sync_single, symbol, interval, limit)
                results[interval] = success
                await asyncio.sleep(0.3)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution(f"sync_crypto_hourly_{symbol}", all(results.values()), execution_time)
            
            return results

        except Exception as e:
            self.logger.error(f"同步 {symbol} K线数据失败: {e}")
            raise

    def get_sync_status(self) -> Dict[str, Any]:
        """获取各币种的同步状态"""
        status = {}
        for symbol in self.SYMBOLS:
            symbol_status = {}
            for interval in self.INTERVALS:
                count = self.orm.get_count(symbol, interval)
                date_range = self.orm.get_date_range(symbol, interval)
                latest = self.orm.get_latest(symbol, interval)
                
                symbol_status[interval] = {
                    "count": count,
                    "date_range": date_range,
                    "latest_close": latest['close'] if latest else None,
                    "latest_timestamp": latest['timestamp'] if latest else None
                }
            status[symbol] = symbol_status
        
        return status


# 单例模式
_crypto_hourly_sync_service_instance = None


def get_crypto_hourly_sync_service() -> CryptoHourlySyncService:
    """获取加密货币小时K线同步服务单例"""
    global _crypto_hourly_sync_service_instance
    if _crypto_hourly_sync_service_instance is None:
        _crypto_hourly_sync_service_instance = CryptoHourlySyncService()
    return _crypto_hourly_sync_service_instance
