# -*- coding: utf-8 -*-
"""
美国市场数据同步任务
同步纳斯达克、标普500指数和美元人民币汇率
"""

import asyncio
from datetime import datetime
from typing import Optional

from utils.core.logger_manager import get_logger
from api.utils.task_utils import task_wrapper, record_task_execution
from data.providers.us_market_provider import get_us_market_provider
from services.orm.us_market_orm import get_us_market_service_orm, get_exchange_rate_service_orm


class USMarketSyncService:
    """美国市场数据同步服务"""

    def __init__(self):
        self.logger = get_logger("us_market_sync_service")
        self.provider = get_us_market_provider()
        self.us_market_service = get_us_market_service_orm()
        self.exchange_rate_service = get_exchange_rate_service_orm()

    @task_wrapper
    async def sync_us_market_data(self) -> bool:
        """
        同步所有美国市场数据（纳斯达克、标普500、美元人民币汇率）
        """
        try:
            start_time = datetime.now()
            self.logger.info("开始同步美国市场数据...")

            # 在线程池中执行数据获取
            market_data = await asyncio.to_thread(self.provider.get_all_us_market_data)

            success_count = 0
            total_count = 0

            # 保存纳斯达克数据
            if market_data.get('nasdaq'):
                total_count += 1
                if self.us_market_service.save_index_data(market_data['nasdaq']):
                    success_count += 1

            # 保存标普500数据
            if market_data.get('sp500'):
                total_count += 1
                if self.us_market_service.save_index_data(market_data['sp500']):
                    success_count += 1

            # 保存美元人民币汇率
            if market_data.get('usdcny'):
                total_count += 1
                if self.exchange_rate_service.save_rate_data(market_data['usdcny']):
                    success_count += 1

            execution_time = (datetime.now() - start_time).total_seconds()
            
            if success_count == total_count and total_count > 0:
                record_task_execution("sync_us_market_data", True, execution_time)
                self.logger.info(f"美国市场数据同步成功: {success_count}/{total_count}")
                return True
            else:
                record_task_execution("sync_us_market_data", False, execution_time)
                self.logger.warning(f"美国市场数据同步部分失败: {success_count}/{total_count}")
                return False

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("sync_us_market_data", False, execution_time)
            self.logger.error(f"美国市场数据同步失败: {e}")
            raise

    @task_wrapper
    async def sync_nasdaq_only(self) -> bool:
        """仅同步纳斯达克指数"""
        try:
            start_time = datetime.now()
            nasdaq_data = await asyncio.to_thread(self.provider.get_nasdaq_data)
            
            if nasdaq_data:
                result = self.us_market_service.save_index_data(nasdaq_data)
                execution_time = (datetime.now() - start_time).total_seconds()
                record_task_execution("sync_nasdaq_only", result, execution_time)
                return result
            
            return False

        except Exception as e:
            self.logger.error(f"纳斯达克数据同步失败: {e}")
            raise

    @task_wrapper
    async def sync_sp500_only(self) -> bool:
        """仅同步标普500指数"""
        try:
            start_time = datetime.now()
            sp500_data = await asyncio.to_thread(self.provider.get_sp500_data)
            
            if sp500_data:
                result = self.us_market_service.save_index_data(sp500_data)
                execution_time = (datetime.now() - start_time).total_seconds()
                record_task_execution("sync_sp500_only", result, execution_time)
                return result
            
            return False

        except Exception as e:
            self.logger.error(f"标普500数据同步失败: {e}")
            raise

    @task_wrapper
    async def sync_usdcny_only(self) -> bool:
        """仅同步美元人民币汇率"""
        try:
            start_time = datetime.now()
            usdcny_data = await asyncio.to_thread(self.provider.get_usdcny_rate)
            
            if usdcny_data:
                result = self.exchange_rate_service.save_rate_data(usdcny_data)
                execution_time = (datetime.now() - start_time).total_seconds()
                record_task_execution("sync_usdcny_only", result, execution_time)
                return result
            
            return False

        except Exception as e:
            self.logger.error(f"美元人民币汇率同步失败: {e}")
            raise


# 单例模式
_us_market_sync_service_instance = None


def get_us_market_sync_service() -> USMarketSyncService:
    """获取美国市场同步服务单例"""
    global _us_market_sync_service_instance
    if _us_market_sync_service_instance is None:
        _us_market_sync_service_instance = USMarketSyncService()
    return _us_market_sync_service_instance
