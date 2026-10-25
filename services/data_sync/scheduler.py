# -*- coding: utf-8 -*-
"""
数据同步调度器
提供定时执行数据同步任务
"""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum

from utils.core.logger_manager import get_logger
from utils.core.config_manager import config_manager
from .sync_manager import DataSyncManager, get_sync_manager, SyncTaskResult

class ScheduleType(Enum):
    """调度类型枚举"""
    INTERVAL = "interval"  # 间隔调度
    CRON = "cron"         # Cron表达式调度
    ONCE = "once"         # 一次性调度

@dataclass
class ScheduleConfig:
    """调度配置"""
    task_name: str
    schedule_type: ScheduleType
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    execute_at: Optional[datetime] = None
    enabled: bool = True
    max_retries: int = 3
    retry_delay_seconds: int = 60

class DataSyncScheduler:
    """数据同步调度器"""

    def __init__(self, sync_manager: Optional[DataSyncManager] = None):
        self.logger = get_logger('data_sync_scheduler')
        self.sync_manager = sync_manager or get_sync_manager()
        self.schedules: Dict[str, ScheduleConfig] = {}
        self.is_running = False
        self.scheduler_thread = None
        self._stop_event = threading.Event()

        # 加载默认调度配置
        self._load_default_schedules()

    def _load_default_schedules(self):
        """加载默认调度配置"""
        try:
            config = config_manager.config
            sync_config = getattr(config, 'config', {}).get('data_sync', {}) if hasattr(config, 'config') else {}
            schedules_config = sync_config.get('schedules', {})

            # 默认调度配置
            default_schedules = {
                'market_data_sync': {
                    'schedule_type': 'interval',
                    'interval_seconds': 300,  # 5分钟
                    'enabled': True
                },
                'market_overview_sync': {
                    'schedule_type': 'interval',
                    'interval_seconds': 300,  # 5分钟
                    'enabled': True
                },
                'coin_details_sync': {
                    'schedule_type': 'interval',
                    'interval_seconds': 3600,  # 1小时
                    'enabled': True
                },
                'fear_greed_sync': {
                    'schedule_type': 'interval',
                    'interval_seconds': 1800,  # 30分钟
                    'enabled': True
                },
                'kline_data_sync': {
                    'schedule_type': 'interval',
                    'interval_seconds': 60,   # 1分钟
                    'enabled': True
                },
                'popular_coins_sync': {
                    'schedule_type': 'interval',
                    'interval_seconds': 900,  # 15分钟
                    'enabled': True
                }
            }

            # 从配置文件中更新设置
            for task_name, default_config in default_schedules.items():
                user_config = schedules_config.get(task_name, {})
                merged_config = {**default_config, **user_config}

                schedule_config = ScheduleConfig(
                    task_name=task_name,
                    schedule_type=ScheduleType(merged_config['schedule_type']),
                    interval_seconds=merged_config.get('interval_seconds'),
                    cron_expression=merged_config.get('cron_expression'),
                    enabled=merged_config.get('enabled', True),
                    max_retries=merged_config.get('max_retries', 3),
                    retry_delay_seconds=merged_config.get('retry_delay_seconds', 60)
                )

                self.schedules[task_name] = schedule_config

        except Exception as e:
            self.logger.error(f"加载调度配置失败: {e}")
            # 使用基本配置
            self._create_basic_schedules()

    def _create_basic_schedules(self):
        """创建基本调度配置"""
        basic_schedules = [
            ('market_data_sync', 300),
            ('coin_details_sync', 3600),
            ('fear_greed_sync', 1800),
            ('kline_data_sync', 60),
            ('popular_coins_sync', 900)
        ]

        for task_name, interval in basic_schedules:
            self.schedules[task_name] = ScheduleConfig(
                task_name=task_name,
                schedule_type=ScheduleType.INTERVAL,
                interval_seconds=interval,
                enabled=True
            )

    def add_schedule(self, schedule_config: ScheduleConfig):
        """添加调度配置"""
        self.schedules[schedule_config.task_name] = schedule_config
        self.logger.info(f"添加调度 {schedule_config.task_name}")

        # 如果调度器正在运行，立即设置调度
        if self.is_running:
            self._setup_schedule(schedule_config)

    def remove_schedule(self, task_name: str):
        """移除调度配置"""
        if task_name in self.schedules:
            del self.schedules[task_name]
            self.logger.info(f"移除调度 {task_name}")

        # 从schedule库中清除任务
        schedule.clear(task_name)

    def enable_schedule(self, task_name: str):
        """启用调度"""
        if task_name in self.schedules:
            self.schedules[task_name].enabled = True
            self.logger.info(f"启用调度 {task_name}")

        if self.is_running:
            self._setup_schedule(self.schedules[task_name])

    def disable_schedule(self, task_name: str):
        """禁用调度"""
        if task_name in self.schedules:
            self.schedules[task_name].enabled = False
            self.logger.info(f"禁用调度 {task_name}")

        # 从schedule库中清除任务
        schedule.clear(task_name)

    def _setup_schedule(self, schedule_config: ScheduleConfig):
        """设置单个调度"""
        if not schedule_config.enabled:
            return

        task_name = schedule_config.task_name

        # 清除现有调度
        schedule.clear(task_name)

        if schedule_config.schedule_type == ScheduleType.INTERVAL:
            if schedule_config.interval_seconds:
                job = schedule.every(schedule_config.interval_seconds).seconds
                job.do(self._execute_scheduled_task, task_name).tag(task_name)
                self.logger.info(f"设置间隔调度: {task_name}, 间隔: {schedule_config.interval_seconds}秒")

        elif schedule_config.schedule_type == ScheduleType.ONCE:
            if schedule_config.execute_at:
                # 计算延迟
                delay = (schedule_config.execute_at - datetime.now()).total_seconds()
                if delay > 0:
                    threading.Timer(delay, self._execute_scheduled_task, args=[task_name]).start()
                    self.logger.info(f"设置一次性调度 {task_name}, 执行时间: {schedule_config.execute_at}")

    def _setup_all_schedules(self):
        """设置所有调度"""
        for schedule_config in self.schedules.values():
            self._setup_schedule(schedule_config)

    def _execute_scheduled_task(self, task_name: str, **kwargs):
        """执行调度任务"""
        try:
            self.logger.info(f"开始执行调度任务 {task_name}")

            # 在线程池中执行异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                result = loop.run_until_complete(self.sync_manager.execute_task(task_name, **kwargs))

                if result.status.value == 'completed':
                    self.logger.info(f"调度任务执行成功: {task_name}")
                else:
                    self.logger.error(f"调度任务执行失败: {task_name}, 错误: {result.error_message}")

                # 如果配置了重试且任务失败
                schedule_config = self.schedules.get(task_name)
                if schedule_config and schedule_config.max_retries > 0:
                    self._retry_task(task_name, schedule_config)

            finally:
                loop.close()

        except Exception as e:
            self.logger.error(f"执行调度任务异常: {task_name}, 错误: {e}")

    def execute_manual_kline_sync(self, timeframe: str, symbols: Optional[List[str]] = None, 
                                limit: int = 100) -> bool:
        """
        手动执行K线数据同步
        
        Args:
            timeframe: 时间框架 (1m, 3m, 5m, 15m, 1h, 1d)
            symbols: 交易对列表
            limit: 数据条数限制
            
        Returns:
            bool: 执行是否成功
        """
        try:
            self.logger.info(f"开始手动执行K线数据同步: {timeframe}, 条数限制: {limit}")

            # 检查是否已有事件循环在运行
            try:
                loop = asyncio.get_running_loop()
                # 如果已有事件循环在运行，在线程池中执行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_manual_kline_sync, timeframe, symbols, limit)
                    return future.result()
            except RuntimeError:
                # 没有事件循环在运行，创建新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        self.sync_manager.execute_manual_kline_sync(timeframe, symbols, limit)
                    ).status.value == 'completed'
                finally:
                    loop.close()

        except Exception as e:
            self.logger.error(f"手动K线数据同步异常: {timeframe}, 错误: {e}")
            return False

    def _run_manual_kline_sync(self, timeframe: str, symbols: Optional[List[str]] = None, 
                              limit: int = 100) -> bool:
        """在线程中运行手动K线数据同步"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.sync_manager.execute_manual_kline_sync(timeframe, symbols, limit)
                )
                return result.status.value == 'completed'
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"线程中执行手动K线数据同步异常: {e}")
            return False

    def execute_manual_all_timeframes_kline_sync(self, symbols: Optional[List[str]] = None, 
                                               limit: int = 100) -> bool:
        """
        手动执行所有时间框架的K线数据同步
        
        Args:
            symbols: 交易对列表
            limit: 每个时间框架的数据条数限制
            
        Returns:
            bool: 执行是否成功
        """
        try:
            self.logger.info(f"开始手动执行所有时间框架K线数据同步，条数限制: {limit}")

            # 检查是否已有事件循环在运行
            try:
                loop = asyncio.get_running_loop()
                # 如果已有事件循环在运行，在线程池中执行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_manual_all_timeframes_kline_sync, symbols, limit)
                    return future.result()
            except RuntimeError:
                # 没有事件循环在运行，创建新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self.sync_manager.execute_manual_all_timeframes_kline_sync(symbols, limit)
                    )
                    return result.status.value == 'completed'
                finally:
                    loop.close()

        except Exception as e:
            self.logger.error(f"手动所有时间框架K线数据同步异常: {e}")
            return False

    def _run_manual_all_timeframes_kline_sync(self, symbols: Optional[List[str]] = None, 
                                            limit: int = 100) -> bool:
        """在线程中运行手动所有时间框架K线数据同步"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.sync_manager.execute_manual_all_timeframes_kline_sync(symbols, limit)
                )
                return result.status.value == 'completed'
            finally:
                loop.close()
        except Exception as e:
            self.logger.error(f"线程中执行手动所有时间框架K线数据同步异常: {e}")
            return False

    def _retry_task(self, task_name: str, schedule_config: ScheduleConfig):
        """重试任务"""
        def retry_func():
            try:
                self.logger.info(f"重试任务: {task_name}")
                self._execute_scheduled_task(task_name)
            except Exception as e:
                self.logger.error(f"重试任务失败: {task_name}, 错误: {e}")

        # 延迟重试
        threading.Timer(schedule_config.retry_delay_seconds, retry_func).start()

    def start(self):
        """启动调度器"""
        if self.is_running:
            self.logger.warning("调度器已在运行")
            return

        self.logger.info("启动数据同步调度器")
        self.is_running = True
        self._stop_event.clear()

        # 设置所有调度
        self._setup_all_schedules()

        # 启动调度器线程
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()

        self.logger.info("数据同步调度器启动完成")

    def stop(self):
        """停止调度器"""
        if not self.is_running:
            self.logger.warning("调度器未运行")
            return

        self.logger.info("停止数据同步调度器")
        self.is_running = False
        self._stop_event.set()

        # 清除所有调度
        schedule.clear()

        # 等待调度器线程结束
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)

        self.logger.info("数据同步调度器停止完成")

    def _run_scheduler(self):
        """运行调度器循环"""
        while self.is_running and not self._stop_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"调度器运行异常 {e}")
                time.sleep(5)  # 异常后等待5秒继续

    def get_schedule_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            'is_running': self.is_running,
            'total_schedules': len(self.schedules),
            'enabled_schedules': sum(1 for s in self.schedules.values() if s.enabled),
            'schedules': {
                name: {
                    'enabled': config.enabled,
                    'schedule_type': config.schedule_type.value,
                    'interval_seconds': config.interval_seconds,
                    'max_retries': config.max_retries
                }
                for name, config in self.schedules.items()
            }
        }

    async def execute_task_now(self, task_name: str) -> SyncTaskResult:
        """立即执行指定任务"""
        self.logger.info(f"立即执行任务: {task_name}")
        return await self.sync_manager.execute_task(task_name)

    async def execute_all_tasks_now(self) -> Dict[str, SyncTaskResult]:
        """立即执行所有任务"""
        self.logger.info("立即执行所有任务")
        return await self.sync_manager.execute_all_tasks()

# 全局调度器实例
_scheduler = None

def get_scheduler() -> DataSyncScheduler:
    """获取全局调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = DataSyncScheduler()
    return _scheduler