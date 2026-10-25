# -*- coding: utf-8 -*-
"""
QDII基金数据同步任务
同步场内QDII基金数据（纳斯达克和标普相关）
"""

import asyncio
from datetime import datetime
from typing import List, Optional

from utils.core.logger_manager import get_logger
from api.utils.task_utils import task_wrapper, record_task_execution
from data.providers.qdii_fund_provider import get_qdii_fund_provider
from services.orm.qdii_fund_orm import get_qdii_fund_service_orm


class QDIIFundSyncService:
    """QDII基金数据同步服务"""

    def __init__(self):
        self.logger = get_logger("qdii_fund_sync_service")
        self.provider = get_qdii_fund_provider()
        self.fund_service = get_qdii_fund_service_orm()

    @task_wrapper
    async def sync_all_qdii_funds(self) -> bool:
        """
        同步所有QDII基金数据
        """
        try:
            start_time = datetime.now()
            self.logger.info("开始同步QDII基金数据...")

            # 在线程池中执行数据获取
            funds_data = await asyncio.to_thread(self.provider.get_all_qdii_funds)

            if not funds_data:
                self.logger.warning("未获取到任何QDII基金数据")
                return False

            # 批量保存
            success_count = self.fund_service.save_multiple_funds(funds_data)

            execution_time = (datetime.now() - start_time).total_seconds()
            
            if success_count == len(funds_data):
                record_task_execution("sync_all_qdii_funds", True, execution_time)
                self.logger.info(f"QDII基金数据同步成功: {success_count}/{len(funds_data)}")
                return True
            else:
                record_task_execution("sync_all_qdii_funds", False, execution_time)
                self.logger.warning(f"QDII基金数据同步部分失败: {success_count}/{len(funds_data)}")
                return False

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("sync_all_qdii_funds", False, execution_time)
            self.logger.error(f"QDII基金数据同步失败: {e}")
            raise

    @task_wrapper
    async def sync_nasdaq_funds(self) -> bool:
        """仅同步纳斯达克相关基金"""
        try:
            start_time = datetime.now()
            self.logger.info("开始同步纳斯达克相关基金...")

            funds_data = await asyncio.to_thread(self.provider.get_nasdaq_funds)

            if not funds_data:
                self.logger.warning("未获取到纳斯达克相关基金数据")
                return False

            success_count = self.fund_service.save_multiple_funds(funds_data)

            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("sync_nasdaq_funds", success_count == len(funds_data), execution_time)
            
            self.logger.info(f"纳斯达克基金同步完成: {success_count}/{len(funds_data)}")
            return success_count == len(funds_data)

        except Exception as e:
            self.logger.error(f"纳斯达克基金同步失败: {e}")
            raise

    @task_wrapper
    async def sync_sp500_funds(self) -> bool:
        """仅同步标普500相关基金"""
        try:
            start_time = datetime.now()
            self.logger.info("开始同步标普500相关基金...")

            funds_data = await asyncio.to_thread(self.provider.get_sp500_funds)

            if not funds_data:
                self.logger.warning("未获取到标普500相关基金数据")
                return False

            success_count = self.fund_service.save_multiple_funds(funds_data)

            execution_time = (datetime.now() - start_time).total_seconds()
            record_task_execution("sync_sp500_funds", success_count == len(funds_data), execution_time)
            
            self.logger.info(f"标普500基金同步完成: {success_count}/{len(funds_data)}")
            return success_count == len(funds_data)

        except Exception as e:
            self.logger.error(f"标普500基金同步失败: {e}")
            raise


# 单例模式
_qdii_fund_sync_service_instance = None


def get_qdii_fund_sync_service() -> QDIIFundSyncService:
    """获取QDII基金同步服务单例"""
    global _qdii_fund_sync_service_instance
    if _qdii_fund_sync_service_instance is None:
        _qdii_fund_sync_service_instance = QDIIFundSyncService()
    return _qdii_fund_sync_service_instance
