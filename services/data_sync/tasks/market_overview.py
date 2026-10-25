# -*- coding: utf-8 -*-
"""
市场概览同步任务
专门用于同步市场概览数据到market_overview表
"""

from typing import Dict, Any, Optional
from datetime import datetime

from utils.core.logger_manager import get_logger
from ..data_sync_service import DataSyncService
from ..sync_manager import BaseSyncTask, SyncTaskResult, SyncTaskStatus


class MarketOverviewSyncTask(DataSyncService, BaseSyncTask):
    """市场概览同步任务"""

    def __init__(self):
        DataSyncService.__init__(self)
        BaseSyncTask.__init__(self, 'market_overview_sync')
        self.logger = get_logger('market_overview_sync_task')

    def get_task_config(self) -> Dict[str, Any]:
        """获取任务配置"""
        return {
            'enabled': True,
            'interval_seconds': 300,  # 5分钟
            'max_retries': 3,
            'retry_delay_seconds': 60
        }

    async def execute(self) -> SyncTaskResult:
        """执行市场概览同步任务"""
        self.logger.info("开始执行市场概览同步任务")
        
        try:
            # 调用父类的sync_market_overview方法
            success = await self.sync_market_overview()
            
            if success:
                self.logger.info("市场概览同步任务执行成功")
                return self._create_result(
                    status=SyncTaskStatus.COMPLETED,
                    records_processed=1,
                    records_inserted=1
                )
            else:
                self.logger.error("市场概览同步任务执行失败")
                return self._create_result(
                    status=SyncTaskStatus.FAILED,
                    error_message="市场概览同步失败"
                )
                
        except Exception as e:
            self.logger.error(f"市场概览同步任务异常: {e}")
            return self._create_result(
                status=SyncTaskStatus.FAILED,
                error_message=str(e)
            )


# 单例模式
_market_overview_sync_task: Optional[MarketOverviewSyncTask] = None

def get_market_overview_sync_task() -> MarketOverviewSyncTask:
    """获取市场概览同步任务单例"""
    global _market_overview_sync_task
    if _market_overview_sync_task is None:
        _market_overview_sync_task = MarketOverviewSyncTask()
    return _market_overview_sync_task

# 兼容保留：以别名方式避免重复实现
create_market_overview_sync_task = get_market_overview_sync_task
get_market_overview_sync_task_instance = get_market_overview_sync_task
