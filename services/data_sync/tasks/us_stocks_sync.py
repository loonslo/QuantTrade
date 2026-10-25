# -*- coding: utf-8 -*-
"""
美股个股数据同步任务
同步11只美股（Magnificent 7 + 核心行业头部）的日K线数据
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List

from utils.core.logger_manager import get_logger
from api.utils.task_utils import task_wrapper, record_task_execution
from data.providers.us_stocks_provider import get_us_stocks_provider
from services.orm.us_stocks_orm import get_us_stocks_service


class USStocksSyncService:
    """美股个股数据同步服务"""

    # 美股7姐妹 + 核心行业头部
    STOCKS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'JPM', 'UNH', 'KO', 'BRK.B']

    def __init__(self):
        self.logger = get_logger("us_stocks_sync_service")
        self.provider = get_us_stocks_provider()
        self.service = get_us_stocks_service()

    @task_wrapper
    async def sync_all_stocks(self, days: int = 365) -> Dict[str, bool]:
        """
        同步所有11只美股的日K线数据
        
        Args:
            days: 获取最近多少天数据，默认365天
            
        Returns:
            Dict: {'AAPL': True, 'MSFT': True, ...}
        """
        try:
            start_time = datetime.now()
            self.logger.info(f"开始同步所有 {len(self.STOCKS)} 只美股...")

            results = {}
            success_list = []
            failed_list = []

            for symbol in self.STOCKS:
                try:
                    # 在线程池中执行同步
                    success = await asyncio.to_thread(self._sync_single, symbol, days)
                    results[symbol] = success
                    
                    if success:
                        success_list.append(symbol)
                        self.logger.info(f"✅ {symbol} 同步成功")
                    else:
                        failed_list.append(symbol)
                        self.logger.warning(f"❌ {symbol} 同步失败")
                    
                    # 避免请求过快
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    self.logger.error(f"同步 {symbol} 时异常: {e}")
                    results[symbol] = False
                    failed_list.append(symbol)

            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 记录任务执行
            all_success = len(failed_list) == 0
            record_task_execution("sync_us_stocks_all", all_success, execution_time)
            
            self.logger.info(f"美股同步完成: 成功 {len(success_list)}, 失败 {len(failed_list)}, 耗时 {execution_time:.2f}s")
            self.logger.info(f"失败的股票: {failed_list}")
            
            return results

        except Exception as e:
            self.logger.error(f"同步所有美股失败: {e}")
            raise

    def _sync_single(self, symbol: str, days: int = 365) -> bool:
        """
        同步单只股票
        
        Args:
            symbol: 股票代码
            days: 获取天数
            
        Returns:
            bool: 是否成功
        """
        try:
            # 获取K线数据
            klines = self.provider.get_daily_ohlcv(symbol, days)
            
            if not klines:
                self.logger.warning(f"未获取到 {symbol} 的K线数据")
                return False
            
            # 保存到数据库
            success = self.service.save_batch_daily_kline(symbol, klines)
            
            return success

        except Exception as e:
            self.logger.error(f"同步 {symbol} 失败: {e}")
            return False

    @task_wrapper
    async def sync_single_stock(self, symbol: str, days: int = 365) -> bool:
        """
        同步单只股票
        
        Args:
            symbol: 股票代码
            days: 获取天数
            
        Returns:
            bool: 是否成功
        """
        try:
            start_time = datetime.now()
            symbol = symbol.upper()
            
            if symbol not in self.STOCKS:
                self.logger.warning(f"{symbol} 不在同步列表中")
            
            self.logger.info(f"开始同步 {symbol} ...")
            
            # 在线程池中执行
            success = await asyncio.to_thread(self._sync_single, symbol, days)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution(f"sync_us_stocks_{symbol}", success, execution_time)
            
            if success:
                self.logger.info(f"✅ {symbol} 同步成功，耗时 {execution_time:.2f}s")
            else:
                self.logger.warning(f"❌ {symbol} 同步失败")
            
            return success

        except Exception as e:
            self.logger.error(f"同步 {symbol} 失败: {e}")
            raise

    def get_sync_status(self) -> Dict[str, Any]:
        """获取各股票的同步状态"""
        status = {}
        for symbol in self.STOCKS:
            count = self.service.get_count(symbol)
            date_range = self.service.get_date_range(symbol)
            latest = self.service.get_latest(symbol)
            
            status[symbol] = {
                "count": count,
                "date_range": date_range,
                "latest_close": latest['close'] if latest else None,
                "latest_date": latest['timestamp'] if latest else None
            }
        
        return status


# 单例模式
_us_stocks_sync_service_instance = None


def get_us_stocks_sync_service() -> USStocksSyncService:
    """获取美股同步服务单例"""
    global _us_stocks_sync_service_instance
    if _us_stocks_sync_service_instance is None:
        _us_stocks_sync_service_instance = USStocksSyncService()
    return _us_stocks_sync_service_instance
