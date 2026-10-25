# -*- coding: utf-8 -*-
"""
数据同步管理器
提供管理所有数据同步任务和调度
"""

from typing import Dict, Any, List, Optional, Union, Type
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from contextlib import contextmanager
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum

from utils.core.logger_manager import get_logger
from utils.helpers.constants import ConfigConstants
from data.types import ServiceResponse
from data.database.session_manager import get_session_manager, ORMBaseService

class SyncTaskStatus(Enum):
    """同步任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class SyncTaskResult:
    """同步任务结果"""
    task_name: str
    status: SyncTaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    records_processed: int = 0
    records_updated: int = 0
    records_inserted: int = 0
    error_message: Optional[str] = None
    execution_time: Optional[float] = None

class BaseSyncTask(ABC):
    """数据同步任务基类"""

    def __init__(self, task_name: str):
        self.task_name = task_name
        self.logger = get_logger(f'sync_task_{task_name}')
        self.status = SyncTaskStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.error_message = None

    @abstractmethod
    async def execute(self) -> SyncTaskResult:
        """执行同步任务"""
        pass

    @abstractmethod
    def get_task_config(self) -> Dict[str, Any]:
        """获取任务配置"""
        pass

    def _create_result(self,
                        status: SyncTaskStatus,
                        records_processed: int = 0,
                        records_updated: int = 0,
                        records_inserted: int = 0,
                        error_message: Optional[str] = None) -> SyncTaskResult:
        """创建任务结果"""
        execution_time = None
        if self.start_time and self.end_time:
            execution_time = (self.end_time - self.start_time).total_seconds()

        return SyncTaskResult(
            task_name=self.task_name,
            status=status,
            start_time=self.start_time,
            end_time=self.end_time,
            records_processed=records_processed,
            records_updated=records_updated,
            records_inserted=records_inserted,
            error_message=error_message,
            execution_time=execution_time
        )

class DataSyncManager:
    """数据同步管理器"""

    def __init__(self, max_workers: int = 4):
        self.logger = get_logger('data_sync_manager')
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: Dict[str, BaseSyncTask] = {}
        self.task_results: Dict[str, SyncTaskResult] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self._lock = threading.Lock()

    def register_task(self, task: BaseSyncTask):
        """注册同步任务"""
        with self._lock:
            self.tasks[task.task_name] = task
            self.logger.info(f"注册任务 {task.task_name}")

    def unregister_task(self, task_name: str):
        """注销同步任务"""
        with self._lock:
            if task_name in self.tasks:
                del self.tasks[task_name]
                self.logger.info(f"注销任务: {task_name}")

    async def execute_task(self, task_name: str, **kwargs) -> SyncTaskResult:
        """执行单个同步任务"""
        start_time = datetime.now()
        
        # 首先检查是否在已注册的任务中
        if task_name in self.tasks:
            task = self.tasks[task_name]
            try:
                self.logger.info(f"开始执行同步任务 {task_name}")
                task.start_time = start_time
                task.status = SyncTaskStatus.RUNNING

                result = await task.execute()

                task.end_time = datetime.now()
                task.status = result.status

                self.task_results[task_name] = result

                if result.status == SyncTaskStatus.COMPLETED:
                    self.logger.info(f"同步任务 {task_name} 执行成功")
                else:
                    self.logger.warning(f"同步任务 {task_name} 执行失败: {result.error_message}")

                return result

            except Exception as e:
                error_msg = f"执行同步任务 {task_name} 时发生异常: {str(e)}"
                self.logger.error(error_msg)
                task.end_time = datetime.now()
                task.status = SyncTaskStatus.FAILED

                result = SyncTaskResult(
                    task_name=task_name,
                    status=SyncTaskStatus.FAILED,
                    start_time=start_time,
                    end_time=datetime.now(),
                    error_message=error_msg
                )
                self.task_results[task_name] = result
                return result
        
        # 期货数据同步任务（方案3：统一表结构）
        if task_name == 'sync_futures_data_v2':
            from .tasks.futures_data_sync_v2 import get_futures_data_sync_service_v2
            service = get_futures_data_sync_service_v2()
            success = await service.sync_futures_data()
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            return SyncTaskResult(
                task_name=task_name,
                status=SyncTaskStatus.COMPLETED if success else SyncTaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                error_message=None if success else "期货数据同步失败"
            )

        # K线数据同步任务
        if task_name == 'sync_market_data_1m':
            from .tasks.kline_data_sync import get_kline_data_sync_service
            service = get_kline_data_sync_service()
            success = await service.sync_kline_data('1m')
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            return SyncTaskResult(
                task_name=task_name,
                status=SyncTaskStatus.COMPLETED if success else SyncTaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                error_message=None if success else "K线数据同步失败"
            )

        elif task_name == 'sync_market_data_3m':
            from .tasks.kline_data_sync import get_kline_data_sync_service
            service = get_kline_data_sync_service()
            success = await service.sync_kline_data('3m')
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            return SyncTaskResult(
                task_name=task_name,
                status=SyncTaskStatus.COMPLETED if success else SyncTaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                error_message=None if success else "K线数据同步失败"
            )

        elif task_name == 'sync_market_data_5m':
            from .tasks.kline_data_sync import get_kline_data_sync_service
            service = get_kline_data_sync_service()
            success = await service.sync_kline_data('5m')
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            return SyncTaskResult(
                task_name=task_name,
                status=SyncTaskStatus.COMPLETED if success else SyncTaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                error_message=None if success else "K线数据同步失败"
            )

        elif task_name == 'sync_market_data_15m':
            from .tasks.kline_data_sync import get_kline_data_sync_service
            service = get_kline_data_sync_service()
            success = await service.sync_kline_data('15m')
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            return SyncTaskResult(
                task_name=task_name,
                status=SyncTaskStatus.COMPLETED if success else SyncTaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                error_message=None if success else "K线数据同步失败"
            )

        elif task_name == 'sync_market_data_1h':
            from .tasks.kline_data_sync import get_kline_data_sync_service
            service = get_kline_data_sync_service()
            success = await service.sync_kline_data('1h')
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            return SyncTaskResult(
                task_name=task_name,
                status=SyncTaskStatus.COMPLETED if success else SyncTaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                error_message=None if success else "K线数据同步失败"
            )

        elif task_name == 'sync_market_data_4h':
            from .tasks.kline_data_sync import get_kline_data_sync_service
            service = get_kline_data_sync_service()
            success = await service.sync_kline_data('4h')
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            return SyncTaskResult(
                task_name=task_name,
                status=SyncTaskStatus.COMPLETED if success else SyncTaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                error_message=None if success else "K线数据同步失败"
            )

        elif task_name == 'sync_market_data_1d':
            from .tasks.kline_data_sync import get_kline_data_sync_service
            service = get_kline_data_sync_service()
            success = await service.sync_kline_data('1d')
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            return SyncTaskResult(
                task_name=task_name,
                status=SyncTaskStatus.COMPLETED if success else SyncTaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                error_message=None if success else "K线数据同步失败"
            )

        # 热门币种和市场概览
        if task_name == 'sync_top_symbols':
            from .data_sync_service import DataSyncService
            service = DataSyncService()
            success = await service.sync_top_symbols()
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            return SyncTaskResult(
                task_name=task_name,
                status=SyncTaskStatus.COMPLETED if success else SyncTaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                error_message=None if success else "同步热门币种失败"
            )

        elif task_name == 'sync_market_overview':
            from .data_sync_service import DataSyncService
            service = DataSyncService()
            success = await service.sync_market_overview()
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            return SyncTaskResult(
                task_name=task_name,
                status=SyncTaskStatus.COMPLETED if success else SyncTaskStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                execution_time=execution_time,
                error_message=None if success else "同步市场概览失败"
            )

        # 如果任务不存在，返回错误
        error_msg = f"任务不存在或未注册: {task_name}"
        self.logger.error(error_msg)
        return SyncTaskResult(
            task_name=task_name,
            status=SyncTaskStatus.FAILED,
            start_time=start_time,
            end_time=datetime.now(),
            error_message=error_msg
        )

    async def execute_tasks(self, task_names: List[str], parallel: bool = True) -> Dict[str, SyncTaskResult]:
        """执行多个同步任务"""
        if not task_names:
            return {}

        if parallel:
            # 并行执行
            tasks = [self.execute_task(name) for name in task_names]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            result_dict = {}
            for i, result in enumerate(results):
                task_name = task_names[i]
                if isinstance(result, Exception):
                    result_dict[task_name] = SyncTaskResult(
                        task_name=task_name,
                        status=SyncTaskStatus.FAILED,
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        error_message=str(result)
                    )
                else:
                    result_dict[task_name] = result

            return result_dict
        else:
            # 串行执行
            results = {}
            for task_name in task_names:
                result = await self.execute_task(task_name)
                results[task_name] = result

                # 如果任务失败且配置了失败时停止，则停止后续任务
                if result.status == SyncTaskStatus.FAILED:
                    self.logger.warning(f"任务 {task_name} 失败，停止后续任务执行")
                    break

            return results

    async def execute_all_tasks(self, parallel: bool = True) -> Dict[str, SyncTaskResult]:
        """执行所有已注册的同步任务"""
        task_names = list(self.tasks.keys())
        return await self.execute_tasks(task_names, parallel)

    def get_task_status(self, task_name: str) -> Optional[SyncTaskStatus]:
        """获取任务状态"""
        if task_name in self.tasks:
            return self.tasks[task_name].status
        return None

    def get_task_result(self, task_name: str) -> Optional[SyncTaskResult]:
        """获取任务结果"""
        return self.task_results.get(task_name)

    def get_all_task_results(self) -> Dict[str, SyncTaskResult]:
        """获取所有任务结果"""
        return self.task_results.copy()

    def clear_task_results(self):
        """清除任务结果"""
        with self._lock:
            self.task_results.clear()

    def get_task_summary(self) -> Dict[str, Any]:
        """获取任务执行摘要"""
        total_tasks = len(self.tasks)
        completed_tasks = sum(1 for result in self.task_results.values()
                              if result.status == SyncTaskStatus.COMPLETED)
        failed_tasks = sum(1 for result in self.task_results.values()
                           if result.status == SyncTaskStatus.FAILED)

        total_records_processed = sum(result.records_processed for result in self.task_results.values())
        total_records_updated = sum(result.records_updated for result in self.task_results.values())
        total_records_inserted = sum(result.records_inserted for result in self.task_results.values())

        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'success_rate': completed_tasks / total_tasks if total_tasks > 0 else 0,
            'total_records_processed': total_records_processed,
            'total_records_updated': total_records_updated,
            'total_records_inserted': total_records_inserted,
            'last_execution': max([result.end_time for result in self.task_results.values()
                                  if result.end_time], default=None)
        }

    def shutdown(self):
        """关闭同步管理器"""
        self.logger.info("正在关闭数据同步管理器...")

        # 取消所有正在运行的任务
        for task_name, task in self.running_tasks.items():
            if not task.done():
                task.cancel()
                self.logger.info(f"取消任务 {task_name}")

        # 关闭线程池
        self.executor.shutdown(wait=True)
        self.logger.info("数据同步管理器已关闭")

    async def execute_manual_kline_sync(self, timeframe: str, symbols: Optional[List[str]] = None, 
                                      limit: int = 100) -> SyncTaskResult:
        """
        手动执行K线数据同步
        
        Args:
            timeframe: 时间框架 (1m, 3m, 5m, 15m, 1h, 1d)
            symbols: 交易对列表
            limit: 数据条数限制
            
        Returns:
            SyncTaskResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            from .tasks.kline_data_sync import get_kline_data_sync_service
            
            self.logger.info(f"开始手动执行K线数据同步: {timeframe}, 条数限制: {limit}")
            
            # 获取K线数据同步服务
            kline_service = get_kline_data_sync_service()
            
            # 验证参数
            if not kline_service.validate_timeframe(timeframe):
                error_msg = f"不支持的时间框架: {timeframe}"
                self.logger.error(error_msg)
                return SyncTaskResult(
                    task_name=f"manual_kline_sync_{timeframe}",
                    status=SyncTaskStatus.FAILED,
                    start_time=start_time,
                    end_time=datetime.now(),
                    error_message=error_msg
                )
            
            is_valid, error_msg = kline_service.validate_limit(timeframe, limit)
            if not is_valid:
                self.logger.error(error_msg)
                return SyncTaskResult(
                    task_name=f"manual_kline_sync_{timeframe}",
                    status=SyncTaskStatus.FAILED,
                    start_time=start_time,
                    end_time=datetime.now(),
                    error_message=error_msg
                )
            
            # 执行手动同步
            success = await kline_service.manual_sync_kline_data(timeframe, symbols, limit)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            if success:
                self.logger.info(f"手动K线数据同步成功: {timeframe}, 耗时 {execution_time:.2f} 秒")
                result = SyncTaskResult(
                    task_name=f"manual_kline_sync_{timeframe}",
                    status=SyncTaskStatus.COMPLETED,
                    start_time=start_time,
                    end_time=end_time,
                    execution_time=execution_time
                )
            else:
                self.logger.warning(f"手动K线数据同步失败: {timeframe}")
                result = SyncTaskResult(
                    task_name=f"manual_kline_sync_{timeframe}",
                    status=SyncTaskStatus.FAILED,
                    start_time=start_time,
                    end_time=end_time,
                    execution_time=execution_time,
                    error_message="同步返回False"
                )
            
            self.task_results[f"manual_kline_sync_{timeframe}"] = result
            return result
            
        except Exception as e:
            error_msg = f"手动K线数据同步异常: {str(e)}"
            self.logger.error(error_msg)
            return SyncTaskResult(
                task_name=f"manual_kline_sync_{timeframe}",
                status=SyncTaskStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=error_msg
            )

    async def execute_manual_all_timeframes_kline_sync(self, symbols: Optional[List[str]] = None, 
                                                     limit: int = 100) -> SyncTaskResult:
        """
        手动执行所有时间框架的K线数据同步
        
        Args:
            symbols: 交易对列表
            limit: 每个时间框架的数据条数限制
            
        Returns:
            SyncTaskResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            from .tasks.kline_data_sync import get_kline_data_sync_service
            
            self.logger.info(f"开始手动执行所有时间框架K线数据同步，条数限制: {limit}")
            
            # 获取K线数据同步服务
            kline_service = get_kline_data_sync_service()
            
            # 执行手动同步
            success = await kline_service.manual_sync_all_timeframes_kline_data(symbols, limit)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            if success:
                self.logger.info(f"手动所有时间框架K线数据同步成功，耗时 {execution_time:.2f} 秒")
                result = SyncTaskResult(
                    task_name="manual_all_timeframes_kline_sync",
                    status=SyncTaskStatus.COMPLETED,
                    start_time=start_time,
                    end_time=end_time,
                    execution_time=execution_time
                )
            else:
                self.logger.warning("手动所有时间框架K线数据同步失败")
                result = SyncTaskResult(
                    task_name="manual_all_timeframes_kline_sync",
                    status=SyncTaskStatus.FAILED,
                    start_time=start_time,
                    end_time=end_time,
                    execution_time=execution_time,
                    error_message="同步返回False"
                )
            
            self.task_results["manual_all_timeframes_kline_sync"] = result
            return result
            
        except Exception as e:
            error_msg = f"手动所有时间框架K线数据同步异常: {str(e)}"
            self.logger.error(error_msg)
            return SyncTaskResult(
                task_name="manual_all_timeframes_kline_sync",
                status=SyncTaskStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=error_msg
            )

# 全局同步管理器实例
_sync_manager = None

def get_sync_manager() -> DataSyncManager:
    """获取全局同步管理器实例"""
    global _sync_manager
    if _sync_manager is None:
        _sync_manager = DataSyncManager()
    return _sync_manager