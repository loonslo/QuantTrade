# -*- coding: utf-8 -*-
"""
数据同步任务初始化
提供各种数据同步任务的注册和管理功能
"""

from utils.core.logger_manager import get_logger
from .sync_manager import get_sync_manager
from .scheduler import get_scheduler
from .tasks import (
    get_market_overview_sync_task,
    get_crypto_market_rankings_sync_task,
)


def initialize_data_sync_tasks():
    """初始化所有数据同步任务"""
    logger = get_logger('data_sync_init')

    try:
        # 获取管理器和调度器
        sync_manager = get_sync_manager()
        scheduler = get_scheduler()

        # 注册所有任务
        tasks = [
            get_market_overview_sync_task(),
            get_crypto_market_rankings_sync_task()
        ]

        for task in tasks:
            sync_manager.register_task(task)
            logger.info(f"注册任务 {task.task_name}")

        # 添加K线数据同步任务的调度配置
        from .scheduler import ScheduleConfig, ScheduleType
        
        kline_tasks = [
            ('sync_market_data_1m', 60),    # 1分钟执行一次
            ('sync_market_data_3m', 180),   # 3分钟执行一次
            ('sync_market_data_5m', 300),   # 5分钟执行一次
            ('sync_market_data_15m', 900),  # 15分钟执行一次
            ('sync_market_data_1h', 3600),  # 1小时执行一次
            ('sync_market_data_4h', 14400), # 4小时执行一次
            ('sync_market_data_1d', 86400), # 1天执行一次
            ('sync_top_symbols', 3600),     # 1小时执行一次
            ('sync_market_overview', 300),  # 5分钟执行一次
            ('cleanup_old_cache', 86400),   # 1天执行一次
            ('database_maintenance', 604800) # 1周执行一次
        ]
        
        for task_name, interval_seconds in kline_tasks:
            schedule_config = ScheduleConfig(
                task_name=task_name,
                schedule_type=ScheduleType.INTERVAL,
                interval_seconds=interval_seconds,
                enabled=True,
                max_retries=3,
                retry_delay_seconds=60
            )
            scheduler.add_schedule(schedule_config)
            logger.info(f"添加调度任务 {task_name} (间隔: {interval_seconds}秒)")

        logger.info(f"数据同步任务初始化完成，共注册 {len(tasks)} 个任务，添加 {len(kline_tasks)} 个调度任务")

        return sync_manager, scheduler

    except Exception as e:
        logger.error(f"数据同步任务初始化失败: {e}")
        raise

def start_data_sync_scheduler():
    """启动数据同步调度器"""
    logger = get_logger('data_sync_scheduler')

    try:
        # 初始化任务
        sync_manager, scheduler = initialize_data_sync_tasks()

        # 启动调度器
        scheduler.start()

        logger.info("数据同步调度器启动")
        return scheduler

    except Exception as e:
        logger.error(f"启动数据同步调度器失败: {e}")
        raise

def stop_data_sync_scheduler():
    """停止数据同步调度器"""
    logger = get_logger('data_sync_scheduler')

    try:
        scheduler = get_scheduler()
        scheduler.stop()

        sync_manager = get_sync_manager()
        sync_manager.shutdown()

        logger.info("数据同步调度器停止")

    except Exception as e:
        logger.error(f"停止数据同步调度器失败: {e}")
        raise

async def execute_all_sync_tasks():
    """执行所有同步任务"""
    logger = get_logger('data_sync_execute')

    try:
        # 初始化任务
        sync_manager, _ = initialize_data_sync_tasks()

        # 执行所有任务
        results = await sync_manager.execute_all_tasks()

        # 输出执行结果
        summary = sync_manager.get_task_summary()
        logger.info(f"同步任务执行完成: {summary}")

        return results

    except Exception as e:
        logger.error(f"执行同步任务失败: {e}")
        raise

if __name__ == "__main__":
    import asyncio

    # 测试执行所有同步任务
    asyncio.run(execute_all_sync_tasks())